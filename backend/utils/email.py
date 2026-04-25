import os
import smtplib
from email.message import EmailMessage # pylint: disable=no-name-in-module

# SMTP settings from environment variables
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "false").lower() == "true"
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "noreply@likehome.com")

def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using the configured SMTP server.
    """
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM_EMAIL
    msg['To'] = to_email

    try:
        # Use SMTP_SSL for port 465, but here we use standard SMTP + starttls for port 587
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USE_TLS:
                server.starttls()
            
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                
            server.send_message(msg)
            print(f"Successfully sent email to {to_email}")
            return True
    except ConnectionRefusedError:
        print(f"[Email Not Sent] Connection refused to {SMTP_HOST}:{SMTP_PORT}. "
              f"Could not send email to {to_email} with subject '{subject}'.")
        return False
    except Exception as exc: # pylint: disable=broad-exception-caught
        print(f"Failed to send email to {to_email}: {exc}")
        return False
