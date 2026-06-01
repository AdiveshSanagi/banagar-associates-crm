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
from sqlalchemy import func, extract, update
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc

import models
import schemas
import auth
from database import engine, get_db

# Automatically verify/generate tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Banagar Associates Backend Gateway", version="1.0.0")

# Global CORS Policy mapping to allow your local frontend files to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup dedicated uploads folder for your gallery files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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

@app.get("/api/public/booked-dates", response_model=List[str])
def get_booked_dates(db: Session = Depends(get_db)):
    """Returns a simple list of taken dates strings so your calendar blocks them in red"""
    active_bookings = db.query(models.Booking.event_date).filter(
        models.Booking.booking_status != models.BookingStatus.cancelled
    ).all()
    return [b.event_date.strftime("%Y-%m-%d") for b in active_bookings]

@app.post("/api/public/bookings", response_model=schemas.BookingResponse)
def create_booking(payload: schemas.BookingCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Handles the Step 4 & 5 User Booking Request"""
    
    existing = db.query(models.Booking).filter(
        models.Booking.event_date == payload.event_date,
        models.Booking.booking_status != models.BookingStatus.cancelled
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="The selected date is already locked by an active booking cycle")

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

@app.get("/api/public/gallery", response_model=List[schemas.GalleryResponse])
def get_gallery(
    venue_category: Optional[models.VenueCategory] = None,
    media_type: Optional[models.MediaType] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Fetches pictures and videos. Supports limit=8 for your home index page."""
    q = db.query(models.GalleryItem)
    if venue_category:
        q = q.filter(models.GalleryItem.venue_category == venue_category)
    if media_type:
        q = q.filter(models.GalleryItem.media_type == media_type)
    
    q = q.order_by(models.GalleryItem.uploaded_at.desc())
    if limit:
        q = q.limit(limit)
        
    return q.all()



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
    # Add Advance (25k) for Confirmed + Full Rent for Completed bookings
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

# completed booking

# =========================================================
# PROTECTED ADMINISTRATIVE ENDPOINTS (Admin Dashboard)
# =========================================================

@app.get("/api/admin/bookings/completed", response_model=List[schemas.BookingResponse])
def get_completed_bookings(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    completed = db.query(models.Booking)\
        .filter(models.Booking.booking_status == models.BookingStatus.completed)\
        .order_by(models.Booking.event_date.desc())\
        .all()
    return completed



# month wise calculation of revenue for the dashboard analytics page

@app.get("/api/admin/dashboard/monthly-revenue")
def get_monthly_revenue(db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Calculates total revenue grouped by Year and Month"""
    
    # We ask the database to group by Year and Month, and sum the total_amount
    # We only count 'Completed' bookings to keep the accounting accurate
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

    # Format it nicely for the frontend (e.g., "2026-05": 150000)
    formatted_results = []
    for row in revenue_data:
        # Convert month number (5) to padded string ("05")
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
        
    # 🔥 THE NEW DATABASE MATH FIX
    if item.booking_status == models.BookingStatus.completed:
        # If fully paid, move all money to advance_paid and zero out the balance
        item.advance_paid = item.total_amount
        item.balance_left = 0.00
    elif item.booking_status in [models.BookingStatus.confirmed, models.BookingStatus.pending]:
        # If it's just confirmed or pending, lock it back to the 25k advance state
        item.advance_paid = 25000.00
        item.balance_left = float(item.total_amount) - 25000.00
    elif item.booking_status == models.BookingStatus.cancelled:
        # Optional: If cancelled, you can zero everything out or leave it as is for records
        item.advance_paid = 0.00
        item.balance_left = 0.00
        
    db.commit()
    db.refresh(item)
    
    # 🔥 TRIGGER APPROPRIATE ADMIN ACTION NOTIFICATION
    if old_status != item.booking_status:
        if item.booking_status == models.BookingStatus.confirmed:
            background_tasks.add_task(notification.process_booking_notifications, "CONFIRMED", item)
        elif item.booking_status == models.BookingStatus.completed:
            background_tasks.add_task(notification.process_booking_notifications, "COMPLETED", item)
        elif item.booking_status == models.BookingStatus.cancelled:
            background_tasks.add_task(notification.process_booking_notifications, "CANCELLED", item)
            
    return item

@app.get("/api/admin/bookings/date/{event_date_str}", response_model=schemas.BookingResponse)
def get_booking_by_date(event_date_str: str, db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Fetches who booked a date when clicking on a blocked calendar segment"""
    try:
        parsed_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format structure parameter mapping")
        
    item = db.query(models.Booking).filter(
        models.Booking.event_date == parsed_date,
        models.Booking.booking_status != models.BookingStatus.cancelled
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="No active runtime structural allocations discovered on this date context")
    return item

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
    """Handles drag & drop administrative uploads restricting to jpg, png, and mp4 formats"""
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "png", "mp4"]:
        raise HTTPException(status_code=400, detail="Secure system restriction: file extension matrix disallowed")
        
    file_uuid = f"{int(datetime.now().timestamp())}_{file.filename}"
    target_path = os.path.join(UPLOAD_DIR, file_uuid)
    
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    media_url = f"/uploads/{file_uuid}"
    
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

@app.delete("/api/admin/gallery/{item_id}", status_code=200)
def purge_gallery_media(item_id: int, db: Session = Depends(get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Deletes media files completely out of the local folder storage and database records"""
    item = db.query(models.GalleryItem).filter(models.GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Target tracking file object does not exist")
        
    rel_path = item.media_url.lstrip("/")
    if os.path.exists(rel_path):
        os.remove(rel_path)
        
    db.delete(item)
    db.commit()
    return {"message": "System database entry and tracking reference purged clean"}

# update password by admin


class PasswordUpdatePayload(BaseModel):
    key: str = "new_password"
    new_password: str

@app.put("/api/admin/update-password", status_code=200)
def change_admin_password_runtime(payload: PasswordUpdatePayload, current_admin: str = Depends(auth.get_current_admin)):
    # 1. Generate salt and compute secure bcrypt crypt hash sequence
    salt = bcrypt.gensalt(rounds=12)
    new_hash = bcrypt.hashpw(payload.new_password.encode('utf-8'), salt).decode('utf-8')
    
    # 2. Programmatically alter the runtime ecosystem configuration memory mapping
    os.environ["ADMIN_PASSWORD_HASH"] = new_hash
    
    # 💡 Dev Note: To save this permanently to your file system storage so it survives server reboots,
    # we patch your local physical root environment config file right here:
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

