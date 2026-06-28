# =========================================================================
# BANAGAR ASSOCIATES - PRODUCTION NOTIFICATION ENGINE
# Location: /notification.py
# =========================================================================

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- PRODUCTION INFRASTRUCTURE CONFIGURATION ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")  # e.g., your corporate account
SMTP_PASS = os.getenv("SMTP_PASS")  # ⚠️ MUST be a secure 16-character App Password

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@banagarassociates.com")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")  # Standard target format: +91XXXXXXXXXX

# FAST2SMS Integration Layer Configuration
SMS_API_URL = "https://www.fast2sms.com/dev/bulkV2"
SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")

# WHATSAPP SANDBOX/CLOUD API METRICS
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

def send_email(to_email: str, subject: str, body: str):
    """Executes atomic SMTP relays with resilient error trapping."""
    if not SMTP_USER or not SMTP_PASS:
        print("⚠️ [Notification Engine]: SMTP credentials unmapped. Skipping transactional email execution.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Banagar Associates <{SMTP_USER}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"✅ Transactional email successfully relayed to: {to_email}")
    except Exception as e:
        print(f"❌ Critical infrastructure failure during email transmission to {to_email}: {e}")

def send_sms(to_phone: str, message: str):
    """Fires real outbound SMS packages via standardized Fast2SMS API protocols."""
    if not SMS_API_KEY:
        print(f"⚠️ [Fast2SMS Engine Simulation Mode]: {to_phone} -> {message}")
        return

    try:
        # Standard format normalization for Indian telecom boundaries
        clean_number = to_phone.replace("+91", "").replace(" ", "").strip()
        
        payload = {
            "message": message,
            "language": "english",
            "route": "q",  # Fast2SMS Quick Transactional/Inquiry routing
            "numbers": clean_number
        }
        headers = {
            "authorization": SMS_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(SMS_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ Outbound SMS packet acknowledged by gateway for: {clean_number}")
        else:
            print(f"⚠️ Gateway rejected SMS transmission code: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Failed to coordinate payload handshakes with Fast2SMS servers: {e}")

def send_whatsapp(to_phone: str, message_text: str):
    """Coordinates cloud payload deliveries directly into client WhatsApp devices."""
    if not WHATSAPP_TOKEN:
        print(f"💬 [WhatsApp Simulation Mode for {to_phone}]: {message_text}")
        return

    try:
        # WhatsApp Cloud interface requires strict country code strings without '+' signs
        clean_number = to_phone.replace("+", "").replace(" ", "").strip()
        
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_number,
            "type": "text",
            "text": {"preview_url": True, "body": message_text}
        }
        
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=10)
        print(f"✅ WhatsApp dispatch transaction complete. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Critical loop breakage during WhatsApp Cloud dispatch operations: {e}")

def process_booking_notifications(event_type: str, booking):
    """
    Evaluates engine triggers and coordinates asynchronous distribution 
    across all communication vectors (Email, SMS, WhatsApp).
    """
    # Safeguard database models string tracking structures cleanly
    booking_id = getattr(booking, 'id', 'PENDING')
    advance = int(getattr(booking, 'advance_paid', 0))
    balance = int(getattr(booking, 'balance_left', 0))
    date_str = booking.event_date.strftime('%B %d, %Y')
    date_short = booking.event_date.strftime('%b %d')

    if event_type == "NEW_REQUEST":
        # 1. VISITOR INBOUND ROUTES
        user_subject = "Action Required: Banagar Associates Booking Request Received"
        user_body = f"""
        <h3>Hello {booking.customer_name},</h3>
        <p>We have successfully received your reservation application request for <strong>{date_str}</strong> targeting the <strong>{booking.venue_type}</strong> cluster.</p>
        <p>To secure this date in our master ledger, a verified advance payment allocation of <strong>Rs. {advance:,}</strong> is requested.</p>
        <p>Our project management office will contact you immediately via phone to settle this balance clear.</p>
        <br><p>Regards,<br>Corporate Reservations Desk<br><strong>Banagar Associates</strong></p>
        """
        user_msg = f"Banagar Associates: Your booking application for {date_short} is registered. Our management desk will contact you shortly to process your Rs.{advance:,} deposit allocation."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_msg)
        send_whatsapp(booking.phone, user_msg)

        # 2. MANAGEMENT ESCALATION ROUTES
        admin_subject = f"🚨 INTERNAL DISPATCH: New Booking Request - {booking.customer_name}"
        admin_body = f"""
        <h3>Operational Alert: Action Required</h3>
        <p>A new event scheduling request has been submitted to your pipeline:</p>
        <ul>
            <li><strong>Client Identity:</strong> {booking.customer_name}</li>
            <li><strong>Communications Contact:</strong> {booking.phone}</li>
            <li><strong>Target Date:</strong> {date_str}</li>
            <li><strong>Selected Layout:</strong> {booking.venue_type}</li>
        </ul>
        <p>Access your admin interface dashboard immediately to process this user deposit.</p>
        """
        admin_msg = f"CRM NOTICE: New request from {booking.customer_name} for {booking.venue_type} on {date_short}. Contact: {booking.phone}."
        
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        send_sms(ADMIN_PHONE, admin_msg)

    elif event_type == "CONFIRMED":
        user_subject = "TRANSACTION CONFIRMED: Event Space Locked Successfully"
        user_body = f"""
        <div style="border: 1px solid #28a745; padding: 20px; border-radius: 4px;">
            <h2 style="color: #28a745; margin-top:0;">Payment Verification Success</h2>
            <p>Your event allocation for <strong>{date_str}</strong> at <strong>{booking.venue_type}</strong> is officially locked.</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p><strong>Ledger Reference (ID):</strong> {booking_id}</p>
            <p><strong>Advance Deposited:</strong> Rs. {advance:,}</p>
            <p><strong>Remaining Account Balance:</strong> Rs. {balance:,}</p>
        </div>
        """
        user_msg = f"Banagar Associates: Payment verified! Your event reservation (ID: {booking_id}) for {date_short} is officially CONFIRMED. Balance Due: Rs.{balance:,}."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_msg)
        send_whatsapp(booking.phone, user_msg)

    elif event_type == "COMPLETED":
        user_subject = "FINAL CLOSURE RECEIPT: Account Balance Settled"
        user_body = f"""
        <h3>Account Finalization Complete</h3>
        <p>Dear {booking.customer_name}, we have processed your final financial reconciliation step for the event on <strong>{date_str}</strong>.</p>
        <p>Your account records have been marked as fully settled. Thank you for choosing Banagar Associates.</p>
        """
        user_msg = f"Banagar Associates: Final reconciliation processed successfully. Your account folder for booking reference {booking_id} is completely settled and COMPLETED."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_msg)

    elif event_type == "CANCELLED":
        user_subject = "CANCELLATION NOTICE: Booking Reference Expired"
        user_body = f"""
        <h3 style="color: #dc3545;">Reservation Terminated</h3>
        <p>Your booking entry (ID: {booking_id}) allocated for <strong>{date_str}</strong> has been cancelled by administrative command.</p>
        <p>Please contact our operations group immediately for resolution details.</p>
        """
        user_msg = f"Banagar Associates: Notice of cancellation regarding booking reference {booking_id} for {date_short}. Contact our service center for immediate assistance."
        
        send_email(booking.email, user_subject, user_body)
        send_sms(booking.phone, user_msg)
