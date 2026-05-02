import os
import smtplib
from email.message import EmailMessage # pylint: disable=no-name-in-module
from flask import current_app

def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """
    Sends an email using the configured SMTP server.
    Uses current_app.config if available, otherwise falls back to environment variables.
    """
    if current_app:
        # Use config from Flask app if available
        host = current_app.config.get("SMTP_HOST")
        port = current_app.config.get("SMTP_PORT")
        user = current_app.config.get("SMTP_USERNAME")
        password = current_app.config.get("SMTP_PASSWORD")
        use_tls = current_app.config.get("SMTP_USE_TLS", True)
        use_ssl = current_app.config.get("SMTP_USE_SSL", False)
        from_email = current_app.config.get("SMTP_FROM_EMAIL", "noreply@likehome.com")
    else:
        # Fallback to environment variables (e.g. for background jobs without app context)
        host = os.environ.get("SMTP_HOST", "localhost")
        port = int(os.environ.get("SMTP_PORT", 1025))
        user = os.environ.get("SMTP_USERNAME")
        password = os.environ.get("SMTP_PASSWORD")
        use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
        use_ssl = os.environ.get("SMTP_USE_SSL", "false").lower() == "true"
        from_email = os.environ.get("SMTP_FROM_EMAIL", "noreply@likehome.com")

    # If host is empty, we can't send email
    if not host:
        print(f"[Email Not Sent] SMTP_HOST is not configured. Target: {to_email}")
        return False

    msg = EmailMessage()
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype='html')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        # Select the correct SMTP class based on SSL configuration
        if use_ssl:
            server_class = smtplib.SMTP_SSL
        else:
            server_class = smtplib.SMTP

        with server_class(host, port, timeout=10) as server:
            if not use_ssl and use_tls:
                server.starttls()
            
            if user and password:
                server.login(user, password)
                
            server.send_message(msg)
            print(f"Successfully sent email to {to_email}")
            return True
    except ConnectionRefusedError:
        print(f"[Email Not Sent] Connection refused to {host}:{port}. "
              f"Could not send email to {to_email} with subject '{subject}'.")
        return False
    except Exception as exc: # pylint: disable=broad-exception-caught
        print(f"Failed to send email to {to_email} via {host}:{port}: {exc}")
        return False
