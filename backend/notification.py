# =========================================================================
# BANAGAR ASSOCIATES - NOTIFICATION ENGINE
# Location: /notification.py
# =========================================================================

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import models

# --- CONFIGURATION (Set these in your .env file) ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your-email@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "your-app-password")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@banagar.com")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+919876543210")

# SMS Gateway Config (Example using a standard HTTP API like Twilio or Fast2SMS)
SMS_API_URL = os.getenv("SMS_API_URL", "https://api.sms-gateway.com/send")
SMS_API_KEY = os.getenv("SMS_API_KEY", "your_sms_api_key_here")

def send_email(to_email: str, subject: str, body: str):
    """Sends an email using standard SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Connect to server and send
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email successfully sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")

def send_sms(to_phone: str, message: str):
    """Sends an SMS via a generic HTTP API Gateway."""
    try:
        # Example payload (modify based on your specific SMS provider's documentation)
        payload = {
            "sender": "BANAGAR",
            "route": "4",
            "country": "91",
            "numbers": to_phone,
            "message": message
        }
        headers = {
            "authorization": SMS_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Uncomment the line below to actually fire the SMS once you have an API key!
        # response = requests.post(SMS_API_URL, json=payload, headers=headers)
        # print(f"✅ SMS sent to {to_phone}. Response: {response.status_code}")
        
        print(f"✅ [SIMULATED SMS to {to_phone}]: {message}")
    except Exception as e:
        print(f"❌ Failed to send SMS to {to_phone}: {e}")

def process_booking_notifications(event_type: str, booking: models.Booking):
    """
    Main router for all booking-related alerts.
    Formats the messages and triggers the email/SMS functions.
    """
    if event_type == "NEW_REQUEST":
        
        # 1. MESSAGE TO USER
        user_subject = "Action Required: Banagar Associates Booking Request"
        user_body = f"""
        <h3>Hello {booking.customer_name},</h3>
        <p>We have received your reservation request for <strong>{booking.event_date.strftime('%B %d, %Y')}</strong> at <strong>{booking.venue_type}</strong>.</p>
        <p>To officially lock this date in our calendar, an advance payment of <strong>Rs. {int(booking.advance_paid):,}</strong> is required.</p>
        <p>Our manager will contact you shortly to process this payment via UPI or Cash.</p>
        <br><p>Thank you,<br>Banagar Associates Team</p>
        """
        user_sms = f"Banagar Associates: Your booking request for {booking.event_date.strftime('%b %d')} is received. Our manager will call you shortly regarding the Rs.{int(booking.advance_paid)} advance payment."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_sms)

        # 2. MESSAGE TO ADMIN
        admin_subject = f"NEW LEAD: Booking Request from {booking.customer_name}"
        admin_body = f"""
        <h3>New Booking Request Submitted</h3>
        <ul>
            <li><strong>Client:</strong> {booking.customer_name}</li>
            <li><strong>Phone:</strong> {booking.phone}</li>
            <li><strong>Date:</strong> {booking.event_date.strftime('%B %d, %Y')}</li>
            <li><strong>Venue:</strong> {booking.venue_type}</li>
        </ul>
        <p>Log in to the Admin Dashboard to review and collect the advance payment.</p>
        """
        admin_sms = f"NEW LEAD: {booking.customer_name} requested {booking.venue_type} on {booking.event_date.strftime('%b %d')}. Phone: {booking.phone}."
        
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        send_sms(ADMIN_PHONE, admin_sms)

    elif event_type == "CONFIRMED":
        
        # 1. MESSAGE TO USER
        user_subject = "CONFIRMED: Your Event at Banagar Associates"
        user_body = f"""
        <div style="text-align: center;">
            <h2 style="color: #28a745;">Payment Received!</h2>
            <p>Your booking (ID: <strong>{booking.id}</strong>) is officially confirmed.</p>
        </div>
        <hr>
        <ul>
            <li><strong>Date:</strong> {booking.event_date.strftime('%B %d, %Y')}</li>
            <li><strong>Venue:</strong> {booking.venue_type}</li>
            <li><strong>Advance Paid:</strong> Rs. {int(booking.advance_paid):,}</li>
            <li><strong>Balance Due:</strong> Rs. {int(booking.balance_left):,}</li>
        </ul>
        <p>We look forward to hosting your event!</p>
        """
        user_sms = f"Banagar Associates: Payment Received! Your booking {booking.id} for {booking.event_date.strftime('%b %d')} is officially CONFIRMED."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_sms)

        # 2. MESSAGE TO ADMIN
        admin_subject = f"SUCCESS: Booking {booking.id} Confirmed"
        admin_body = f"<p>You have successfully marked booking {booking.id} for {booking.customer_name} as CONFIRMED.</p>"
        admin_sms = f"SUCCESS: Booking {booking.id} for {booking.customer_name} is now CONFIRMED."
        
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        send_sms(ADMIN_PHONE, admin_sms)

    elif event_type == "COMPLETED":
        
        # 1. MESSAGE TO USER
        user_subject = "COMPLETED: Full Payment Received for Your Event"
        user_body = f"""
        <div style="text-align: center;">
            <h2 style="color: #28a745;">Event Fully Paid!</h2>
            <p>Your booking (ID: <strong>{booking.id}</strong>) is completely finalized.</p>
        </div>
        <hr>
        <p>We have received the final payment for your event on <strong>{booking.event_date.strftime('%B %d, %Y')}</strong> at <strong>{booking.venue_type}</strong>.</p>
        <p>Thank you for choosing Banagar Associates!</p>
        """
        user_sms = f"Banagar Associates: Final payment received! Your booking {booking.id} for {booking.event_date.strftime('%b %d')} is fully COMPLETED."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_sms)

        # 2. MESSAGE TO ADMIN
        admin_subject = f"COMPLETED: Booking {booking.id} Fully Paid"
        admin_body = f"<p>You have successfully marked booking {booking.id} for {booking.customer_name} as COMPLETED (Fully Paid).</p>"
        admin_sms = f"COMPLETED: Booking {booking.id} for {booking.customer_name} is marked fully paid."
        
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        send_sms(ADMIN_PHONE, admin_sms)

    elif event_type == "CANCELLED":
        
        # 1. MESSAGE TO USER
        user_subject = "CANCELLED: Banagar Associates Booking Update"
        user_body = f"""
        <div style="text-align: center;">
            <h2 style="color: #dc3545;">Booking Cancelled</h2>
            <p>Your booking request (ID: <strong>{booking.id}</strong>) has been cancelled.</p>
        </div>
        <hr>
        <p>If you believe this is an error or would like to request a new date, please contact our desk.</p>
        """
        user_sms = f"Banagar Associates: Your booking {booking.id} for {booking.event_date.strftime('%b %d')} has been CANCELLED. Contact us for details."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_sms)

        # 2. MESSAGE TO ADMIN
        admin_subject = f"CANCELLED: Booking {booking.id}"
        admin_body = f"<p>You have successfully CANCELLED booking {booking.id} for {booking.customer_name}.</p>"
        admin_sms = f"CANCELLED: Booking {booking.id} for {booking.customer_name} has been cancelled."
        
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        send_sms(ADMIN_PHONE, admin_sms)