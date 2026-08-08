import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app


def send_verification_email(recipient, username, verification_url, locale="tr"):
    host = current_app.config.get("SMTP_HOST", "")
    user = current_app.config.get("SMTP_USER", "")
    password = current_app.config.get("SMTP_PASSWORD", "")
    sender = current_app.config.get("SMTP_FROM", "") or user
    if not host or not user or not password or not sender:
        current_app.logger.error("verification_email_not_configured")
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    if locale == "tr":
        message["Subject"] = "AtlasFind e-posta adresini doğrula"
        message.set_content(
            f"Merhaba {username},\n\nAtlasFind hesabını etkinleştirmek için aşağıdaki bağlantıyı aç:\n\n"
            f"{verification_url}\n\nBu bağlantı 24 saat geçerlidir. Bu hesabı sen oluşturmadıysan mesajı yok sayabilirsin."
        )
    else:
        message["Subject"] = "Verify your AtlasFind email address"
        message.set_content(
            f"Hello {username},\n\nOpen the link below to activate your AtlasFind account:\n\n"
            f"{verification_url}\n\nThis link is valid for 24 hours. Ignore this message if you did not create the account."
        )

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
        current_app.logger.exception("verification_email_send_failed")
        return False
    return True
