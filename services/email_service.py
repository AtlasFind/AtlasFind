import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app


def _send_email(recipient, subject, body):
    """Deliver a transactional message without logging credentials or content."""
    host = current_app.config.get("SMTP_HOST", "")
    user = current_app.config.get("SMTP_USER", "")
    password = current_app.config.get("SMTP_PASSWORD", "")
    sender = current_app.config.get("SMTP_FROM", "") or user
    if not host or not user or not password or not sender:
        current_app.logger.error("transactional_email_not_configured")
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    port = int(current_app.config.get("SMTP_PORT", 465))
    try:
        if current_app.config.get("SMTP_USE_SSL", True):
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=15) as smtp:
                smtp.login(user, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(user, password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        current_app.logger.exception("transactional_email_send_failed")
        return False
    return True


def send_verification_email(recipient, username, verification_url, locale="tr"):
    if locale == "tr":
        subject = "AtlasFind e-posta adresini doğrula"
        body = (f"Merhaba {username},\n\nAtlasFind hesabını etkinleştirmek için aşağıdaki bağlantıyı aç:\n\n"
                f"{verification_url}\n\nBu bağlantı 24 saat geçerlidir. Bu hesabı sen oluşturmadıysan mesajı yok sayabilirsin.")
    else:
        subject = "Verify your AtlasFind email address"
        body = (f"Hello {username},\n\nOpen the link below to activate your AtlasFind account:\n\n"
                f"{verification_url}\n\nThis link is valid for 24 hours. Ignore this message if you did not create the account.")
    return _send_email(recipient, subject, body)


def send_password_reset_email(recipient, username, reset_url, locale="tr"):
    if locale == "tr":
        subject = "AtlasFind şifreni sıfırla"
        body = (f"Merhaba {username},\n\nAtlasFind şifreni yenilemek için aşağıdaki bağlantıyı aç:\n\n"
                f"{reset_url}\n\nBu bağlantı 1 saat geçerlidir ve yalnızca bir kez kullanılabilir. "
                "Bu isteği sen yapmadıysan mesajı yok sayabilirsin.")
    else:
        subject = "Reset your AtlasFind password"
        body = (f"Hello {username},\n\nOpen the link below to set a new AtlasFind password:\n\n"
                f"{reset_url}\n\nThis link is valid for one hour and can only be used once. "
                "Ignore this message if you did not request it.")
    return _send_email(recipient, subject, body)
