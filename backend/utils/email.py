import os
import smtplib
from email.message import EmailMessage  # pylint: disable=no-name-in-module

from flask import current_app, has_app_context


def _config(name: str, default=None):
    if has_app_context():
        return current_app.config.get(name, default)
    return os.environ.get(name, default)


def _config_flag(name: str, default: bool = False) -> bool:
    raw = _config(name)
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email using the configured SMTP provider."""
    smtp_host = _config("SMTP_HOST", "")
    smtp_port = int(_config("SMTP_PORT", 0) or 0)
    smtp_username = _config("SMTP_USERNAME", "")
    smtp_password = _config("SMTP_PASSWORD", "")
    from_email = _config("SMTP_FROM_EMAIL", smtp_username or "noreply@likehome.local")
    use_tls = _config_flag("SMTP_USE_TLS", True)
    use_ssl = _config_flag("SMTP_USE_SSL", False)

    if not smtp_host or not smtp_port or not to_email:
        print(
            f"[Email Not Sent] Missing SMTP configuration for subject '{subject}'."
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(body)

    try:
        smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_cls(smtp_host, smtp_port, timeout=15) as server:
            if use_tls and not use_ssl:
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(message)
        print(f"Successfully sent email to {to_email}")
        return True
    except ConnectionRefusedError:
        print(
            f"[Email Not Sent] Connection refused to {smtp_host}:{smtp_port}. "
            f"Could not send email to {to_email} with subject '{subject}'."
        )
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Failed to send email to {to_email}: {exc}")
        return False
