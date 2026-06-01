from sqlalchemy import Column, Integer, String, Text, Date, Numeric, DateTime, Enum, func
from database import Base
import enum

# 1. FIXED ENUMS TO MATCH FRONTEND STRINGS EXACTLY
class VenueType(str, enum.Enum):
    lawns = "Banagar Lawns"
    hall = "Banagar Marriage Hall"
    combo = "Combo" 

class PaymentStatus(str, enum.Enum):
    advance = "Advance Paid"
    full = "Fully Paid"

class BookingStatus(str, enum.Enum):
    pending = "Pending"
    confirmed = "Confirmed"
    cancelled = "Cancelled"
    completed = "Completed"

class QueryStatus(str, enum.Enum):
    not_contacted = "Not Contacted"
    contacted = "Contacted"

class MediaType(str, enum.Enum):
    image = "image"
    video = "video"

class VenueCategory(str, enum.Enum):
    lawns = "Lawns"
    hall = "Marriage Hall"
    combo = "Combo"

# 2. THE MASTER BOOKING TABLE
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(20), primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False)
    venue_type = Column(String(100), nullable=False)
    
    # NEW COLUMN ADDED FOR ADMIN DASHBOARD
    event_type = Column(String(100), nullable=True, default="Not Specified") 
    
    event_date = Column(Date, nullable=False, unique=True)
    guest_count = Column(Integer, nullable=False, default=0)
    special_requests = Column(Text, nullable=True)
    advance_paid = Column(Numeric(10, 2), nullable=False, default=25000.00)
    total_amount = Column(Numeric(10, 2), nullable=False, default=150000.00)
    balance_left = Column(Numeric(10, 2), nullable=False, default=125000.00)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.advance)
    booking_status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.pending)
    created_at = Column(DateTime, default=func.now())

# 3. OTHER TABLES (Unchanged)
class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    received_time = Column(DateTime, default=func.now())
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False)
    event_date = Column(Date, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(QueryStatus), nullable=False, default=QueryStatus.not_contacted)

class GalleryItem(Base):
    __tablename__ = "gallery"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    media_url = Column(String(255), nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    venue_category = Column(Enum(VenueCategory), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=func.now())