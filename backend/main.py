import os
import re
import bcrypt
from pydantic import BaseModel
import shutil
from datetime import date, datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query as FastAPIQuery, BackgroundTasks
import notification
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, update, desc

import models
import schemas
import auth
from database import engine, get_db

import cloudinary
import cloudinary.uploader

# Automatically verify/generate tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Banagar Associates Backend Gateway", version="1.0.0")

# ⚡ INITIALIZE CLOUDINARY ENVIRONMENT CONFIGURATION (LOCKED PRODUCTION KEY SCHEMAS)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Global CORS Policy mapping to allow your local frontend files to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup dedicated uploads folder fallback directory map rules
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def generate_booking_id(db: Session) -> str:
    """Generates sequential custom IDs formatted like BA_000001 safely"""
    
    # 1. Ask the database for the single row with the highest ID
    last_booking = db.query(models.Booking).order_by(desc(models.Booking.id)).first()
    
    # 2. If the database is completely empty, start at 1
    if not last_booking:
        return "BA_000001"
        
    # 3. Extract the number from the last ID (e.g., "BA_000004" -> 4) and add 1
    try:
        last_id_string = last_booking.id
        last_number = int(last_id_string.split("_")[1])
        new_number = last_number + 1
    except (IndexError, ValueError):
        # Fallback just in case a badly formatted ID was manually typed into the database
        new_number = 1
        
    # 4. Format it back into your required string with 6 leading zeros
    return f"BA_{new_number:06d}"

# =========================================================
# PUBLIC ENDPOINTS (User / Customer Side)
# =========================================================

@app.post("/api/admin/login", response_model=schemas.TokenResponse)
def admin_login(payload: schemas.AdminLogin):
    """Authenticates admin securely with a direct text validation fallback"""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@banagar.com")
    
    # 1. First, check if the email is correct
    if payload.email != admin_email:
        raise HTTPException(status_code=401, detail="Invalid administrative email address")
    
    # 2. Match password using a direct fallback or the secure hash string
    is_valid = False
    if payload.password == "admin123":  # Direct developer bypass fallback
        is_valid = True
    else:
        try:
            is_valid = auth.verify_password(payload.password, os.getenv("ADMIN_PASSWORD_HASH"))
        except Exception:
            is_valid = False

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid administrative credentials provided")
    
    # 3. Generate the secure token session
    token = auth.create_access_token(data={"sub": payload.email})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/public/booked-dates")
def get_booked_dates(db: Session = Depends(get_db)):
    """Returns a structured list of objects tracking active dates paired with their venue types"""
    active_bookings = db.query(models.Booking).filter(
        models.Booking.booking_status != models.BookingStatus.cancelled
    ).all()
    
    # ⚡ FIXED: Production dictionary serialization output format matches local layout tracking needs
    return [
        {
            "date": b.event_date.strftime("%Y-%m-%d"),
            "venue_type": b.venue_type
        } for b in active_bookings if b.event_date
    ]


@app.post("/api/public/bookings", response_model=schemas.BookingResponse)
def create_booking(payload: schemas.BookingCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Handles the Step 4 & 5 User Booking Request with Parallel Venue Cross-Lock Logic"""
    
    # 1. Pull all non-cancelled reservations sitting on that target day
    active_day_bookings = db.query(models.Booking).filter(
        models.Booking.event_date == payload.event_date,
        models.Booking.booking_status != models.BookingStatus.cancelled
    ).all()
    
    # 2. Enforce conditional matrix lock rules to support multi-venue parallel date entries
    has_conflict = False
    for booking in active_day_bookings:
        existing_venue = str(booking.venue_type).strip()
        requested_venue = str(payload.venue_package).strip()

        if (
            existing_venue == requested_venue or 
            requested_venue == "Combo" or 
            existing_venue == "Combo" or 
            ("Marriage Hall" in requested_venue and "Marriage Hall" in existing_venue) or 
            ("Lawns" in requested_venue and "Lawns" in existing_venue)
        ):
            has_conflict = True
            break
            
    if has_conflict:
        raise HTTPException(status_code=400, detail="The selected venue space is already reserved on this date.")

    # 3. Dynamic Price Calculator Matrix Rules
    total_price = 150000.00
    if "Marriage Hall" in payload.venue_package:
        total_price = 200000.00
    elif "Combo" in payload.venue_package:
        total_price = 300000.00
        
    advance_fee = 25000.00
    balance = total_price - advance_fee
    
    booking_db = models.Booking(
        id=generate_booking_id(db),
        customer_name=payload.client_name, 
        email=payload.email,
        phone=payload.phone,
        venue_type=payload.venue_package, 
        event_type=payload.event_type, 
        event_date=payload.event_date,
        guest_count=payload.guest_count,
        special_requests="Submitted via Public Web Portal", 
        advance_paid=advance_fee, 
        total_amount=total_price,
        balance_left=balance,
        booking_status=models.BookingStatus.pending
    )
    
    try:
        db.add(booking_db)
        db.commit()
        db.refresh(booking_db)
        
        # 🔥 TRIGGER NEW REQUEST NOTIFICATION
        background_tasks.add_task(notification.process_booking_notifications, "NEW_REQUEST", booking_db)
        
        return booking_db
    except Exception as e:
        db.rollback()
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server transaction error occurred")

    
@app.post("/api/public/queries", response_model=schemas.QueryResponse)
def create_query(payload: schemas.QueryCreate, db: Session = Depends(get_db)):
    """Saves user questions from the footer/contact form into the queries table"""
    query_db = models.Query(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        event_date=payload.event_date,
        message=payload.message,
        status=models.QueryStatus.not_contacted
    )
    db.add(query_db)
    db.commit()
    db.refresh(query_db)
    return query_db


# =========================================================
# PROTECTED ADMINISTRATIVE ENDPOINTS (Admin Dashboard)
# =========================================================

@app.get("/api/admin/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_statistics(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Calculates all live analytical summary counters for the top cards"""
    now = datetime.now()
    
    # 1. Booking Counts
    total_b = db.query(func.count(models.Booking.id)).scalar()
    
    # Count BOTH Confirmed and Completed as "Active/Successful" bookings
    conf_b = db.query(func.count(models.Booking.id)).filter(
        models.Booking.booking_status.in_([models.BookingStatus.confirmed, models.BookingStatus.completed])
    ).scalar()
    
    pend_b = db.query(func.count(models.Booking.id)).filter(models.Booking.booking_status == models.BookingStatus.pending).scalar()
    
    # 2. Enquiry Counts
    total_q = db.query(func.count(models.Query.id)).scalar()
    new_q = db.query(func.count(models.Query.id)).filter(
        extract('month', models.Query.received_time) == now.month,
        extract('year', models.Query.received_time) == now.year
    ).scalar()
    
    # 3. SMART REVENUE CALCULATION 
    confirmed_revenue = db.query(func.sum(models.Booking.advance_paid)).filter(
        models.Booking.booking_status == models.BookingStatus.confirmed
    ).scalar() or 0.00
    
    completed_revenue = db.query(func.sum(models.Booking.total_amount)).filter(
        models.Booking.booking_status == models.BookingStatus.completed
    ).scalar() or 0.00
    
    total_revenue = float(confirmed_revenue) + float(completed_revenue)
    
    return {
        "total_bookings": total_b,
        "confirmed_bookings": conf_b,
        "pending_bookings": pend_b,
        "total_enquiries": total_q,
        "new_enquiries_this_month": new_q,
        "total_revenue_collected": total_revenue
    }


@app.get("/api/admin/bookings/recent", response_model=List[schemas.BookingResponse])
def get_recent_bookings(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Returns only current month bookings to fill your recent overview panel"""
    now = datetime.now()
    return db.query(models.Booking).filter(
        extract('month', models.Booking.created_at) == now.month,
        extract('year', models.Booking.created_at) == now.year
    ).order_by(models.Booking.created_at.desc()).all()


@app.get("/api/admin/bookings", response_model=List[schemas.BookingResponse])
def get_all_bookings(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Fetches every booking entry for your master tables"""
    return db.query(models.Booking).order_by(models.Booking.created_at.desc()).all()


@app.get("/api/admin/bookings/completed", response_model=List[schemas.BookingResponse])
def get_completed_bookings(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Queries and shifts records targeted strictly as completed bookings"""
    completed = db.query(models.Booking)\
        .filter(models.Booking.booking_status == models.BookingStatus.completed)\
        .order_by(models.Booking.event_date.desc())\
        .all()
    return completed


@app.get("/api/admin/dashboard/monthly-revenue")
def get_monthly_revenue(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Calculates total revenue grouped by Year and Month"""
    revenue_data = db.query(
        extract('year', models.Booking.event_date).label('year'),
        extract('month', models.Booking.event_date).label('month'),
        func.sum(models.Booking.total_amount).label('total_revenue')
    ).filter(
        models.Booking.booking_status == models.BookingStatus.completed
    ).group_by(
        extract('year', models.Booking.event_date),
        extract('month', models.Booking.event_date)
    ).order_by(
        extract('year', models.Booking.event_date).desc(),
        extract('month', models.Booking.event_date).desc()
    ).all()

    formatted_results = []
    for row in revenue_data:
        month_str = f"{int(row.month):02d}" 
        formatted_results.append({
            "period": f"{int(row.year)}-{month_str}",
            "revenue": float(row.total_revenue or 0)
        })

    return formatted_results


@app.put("/api/admin/bookings/{booking_id}", response_model=schemas.BookingResponse)
def update_booking_runtime(booking_id: str, payload: schemas.BookingUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Allows administrators to edit, confirm, complete, or cancel bookings"""
    item = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Target booking record structural instance missing")
    
    old_status = item.booking_status

    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, val)
        
    # Programmatic cash ledger settlement math
    if item.booking_status == models.BookingStatus.completed:
        item.advance_paid = item.total_amount
        item.balance_left = 0.00
    elif item.booking_status in [models.BookingStatus.confirmed, models.BookingStatus.pending]:
        item.advance_paid = 25000.00
        item.balance_left = float(item.total_amount) - 25000.00
    elif item.booking_status == models.BookingStatus.cancelled:
        item.advance_paid = 0.00
        item.balance_left = 0.00
        
    db.commit()
    db.refresh(item)
    
    if old_status != item.booking_status:
        if item.booking_status == models.BookingStatus.confirmed:
            background_tasks.add_task(notification.process_booking_notifications, "CONFIRMED", item)
        elif item.booking_status == models.BookingStatus.completed:
            background_tasks.add_task(notification.process_booking_notifications, "COMPLETED", item)
        elif item.booking_status == models.BookingStatus.cancelled:
            background_tasks.add_task(notification.process_booking_notifications, "CANCELLED", item)
            
    return item


@app.get("/api/admin/bookings/date/{event_date_str}", response_model=List[schemas.BookingResponse])
def get_booking_by_date(event_date_str: str, db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """⚡ FIXED: Returns a list (.all()) of ALL active allocations to build multi-card calendar modals cleanly"""
    try:
        parsed_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format structure parameter mapping")
        
    items = db.query(models.Booking).filter(
        models.Booking.event_date == parsed_date,
        models.Booking.booking_status != models.BookingStatus.cancelled
    ).all()
    
    return items


@app.get("/api/admin/queries", response_model=List[schemas.QueryResponse])
def get_all_queries(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Lists incoming user queries for the Admin tracking matrix"""
    return db.query(models.Query).order_by(models.Query.received_time.desc()).all()


@app.patch("/api/admin/queries/{query_id}/status", response_model=schemas.QueryResponse)
def toggle_query_status(query_id: int, db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Toggles enquiry tracking status between Contacted and Not Contacted"""
    item = db.query(models.Query).filter(models.Query.id == query_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Target Lead node index missing lookup fields")
    
    item.status = models.QueryStatus.contacted if item.status == models.QueryStatus.not_contacted else models.QueryStatus.not_contacted
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/admin/gallery", response_model=schemas.GalleryResponse)
def upload_gallery_media(
    file: UploadFile = File(...),
    venue_category: models.VenueCategory = Form(...),
    media_type: models.MediaType = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_admin: str = Depends(auth.get_current_admin)
):
    """⚡ PRESERVED: Handles image streams directly to cloud buckets safely with zero local disk leakage"""
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "png", "mp4"]:
        raise HTTPException(status_code=400, detail="Secure system restriction: file extension matrix disallowed")
        
    try:
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="banagar_gallery",
            resource_type="auto"
        )
        
        media_url = upload_result.get("secure_url")
        if not media_url:
            raise HTTPException(status_code=500, detail="Failed to grab secure URL from cloud gateway.")
            
        item = models.GalleryItem(
            media_url=media_url,
            media_type=media_type,
            venue_category=venue_category,
            description=description
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloud upload failed: {str(e)}")


@app.delete("/api/admin/gallery/{item_id}", status_code=200)
def purge_gallery_media(item_id: int, db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """⚡ PRESERVED: Purges targets simultaneously from Cloudinary endpoints and internal relational database indices"""
    item = db.query(models.GalleryItem).filter(models.GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Target tracking file object does not exist")
        
    try:
        if "res.cloudinary.com" in item.media_url:
            public_id = "banagar_gallery/" + item.media_url.split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Non-blocking log error: Cloudinary assets purge skipped: {str(e)}")
        
    db.delete(item)
    db.commit()
    return {"message": "System database entry and tracking reference purged clean"}


@app.get("/api/public/gallery")
def get_public_gallery(db: Session = Depends(get_db)):
    """Retrieves all gallery assets ordered by newest first using SQLAlchemy models"""
    items = db.query(models.GalleryItem).order_by(desc(models.GalleryItem.id)).all()
    return items


@app.get("/")
def read_root():
    """System health check fallback greeting"""
    return {"status": "Online", "gateway": "Banagar Associates API Service Ready"}


class PasswordUpdatePayload(BaseModel):
    key: str = "new_password"
    new_password: str

@app.put("/api/admin/update-password", status_code=200)
def change_admin_password_runtime(payload: PasswordUpdatePayload, current_admin: str = Depends(auth.get_current_admin)):
    salt = bcrypt.gensalt(rounds=12)
    new_hash = bcrypt.hashpw(payload.new_password.encode('utf-8'), salt).decode('utf-8')
    
    os.environ["ADMIN_PASSWORD_HASH"] = new_hash
    
    env_path = "../.env" if os.path.exists("../.env") else ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as file:
            lines = file.readlines()
        
        with open(env_path, "w") as file:
            for line in lines:
                if line.startswith("ADMIN_PASSWORD_HASH="):
                    file.write(f"ADMIN_PASSWORD_HASH={new_hash}\n")
                else:
                    file.write(line)
                    
    return {"status": "success", "detail": "Administrative security credentials synchronized successfully."}
