import smtplib
from email.message import EmailMessage # pylint: disable=no-name-in-module

SMTP_HOST = "localhost"
SMTP_PORT = 1025 # Common testing port for python -m smtpd -n -c DebuggingServer localhost:1025

def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using the local SMTP server.
    Raises ConnectionRefusedError if the SMTP server is not running, 
    but we catch it to prevent the job from failing if the user hasn't started the server.
    """
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = "noreply@likehome.com"
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)
            print(f"Successfully sent email to {to_email}")
    except ConnectionRefusedError:
        print(f"[Email Not Sent] Connection refused to {SMTP_HOST}:{SMTP_PORT}. "
              f"Could not send email to {to_email} with subject '{subject}'.")
    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Failed to send email to {to_email}: {e}")
