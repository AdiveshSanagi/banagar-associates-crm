from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, Union # ⚡ Union added for type safety validation fallbacks
from models import VenueType, BookingStatus, QueryStatus, MediaType, VenueCategory

# --- ADMIN LOGIN VALIDATION ---
class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# --- CUSTOMER BOOKING VALIDATION ---
# Matches the exact JSON payload structured from your frontend files
class BookingCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100)
    email: str # Handled as raw string to accept "Not Provided" text entries cleanly from JS
    phone: str = Field(..., min_length=10, max_length=20)
    venue_package: str 
    event_type: str 
    event_date: date
    guest_count: int = Field(..., ge=0) 
    status: str = "Pending"

class BookingUpdate(BaseModel):
    customer_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    booking_status: Optional[BookingStatus] = None

# --- ENHANCED TYPE-SAFETY FOR PRODUCTION READ ENGINE ---
class BookingResponse(BaseModel):
    id: str
    customer_name: str
    email: str
    phone: str
    # ⚡ CRITICAL FIX: Allows database string tracking values to fall back gracefully 
    # to standard strings if they mismatch the explicit ENUM definitions
    venue_type: Union[VenueType, str] 
    event_type: Optional[str] 
    event_date: date
    guest_count: int
    special_requests: Optional[str]
    advance_paid: float
    total_amount: float
    balance_left: float
    booking_status: BookingStatus
    created_at: datetime

    class Config:
        from_attributes = True

# --- CONTACT/QUERY VALIDATION ---
class QueryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    event_date: date
    message: str

class QueryResponse(BaseModel):
    id: int
    received_time: datetime
    name: str
    phone: str
    email: str
    event_date: date
    message: str
    status: QueryStatus

    class Config:
        from_attributes = True

# --- GALLERY VALIDATION ---
class GalleryResponse(BaseModel):
    id: int
    media_url: str
    media_type: MediaType
    venue_category: VenueCategory
    description: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

# --- ADMIN DASHBOARD CARD ANALYTICS ---
class DashboardStats(BaseModel):
    total_bookings: int
    confirmed_bookings: int
    pending_bookings: int
    total_enquiries: int
    new_enquiries_this_month: int
    total_revenue_collected: float
