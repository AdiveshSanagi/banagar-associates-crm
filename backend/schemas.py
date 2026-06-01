from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional
from models import VenueType, BookingStatus, QueryStatus, MediaType, VenueCategory

# --- ADMIN LOGIN VALIDATION ---
class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# --- CUSTOMER BOOKING VALIDATION ---
# UPDATED: Matches the exact JSON payload sent from booking.html
class BookingCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100)
    email: str # Changed from EmailStr to allow the "Not Provided" fallback from JS
    phone: str = Field(..., min_length=10, max_length=20)
    venue_package: str # Takes the string from JS (e.g., "Banagar Lawns")
    event_type: str # <-- ADDED: The new event type field
    event_date: date
    guest_count: int = Field(..., ge=0) # ge=0 since JS defaults to 0 if left blank
    status: str = "Pending"

class BookingUpdate(BaseModel):
    customer_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    booking_status: Optional[BookingStatus] = None

# UPDATED: Added event_type so the Admin Dashboard can read it back from the DB
class BookingResponse(BaseModel):
    id: str
    customer_name: str
    email: str
    phone: str
    venue_type: VenueType
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