import os
import smtplib
import logging
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)


def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    attachment: Path,
):
    logger.error("SMTP SEND START")
    logger.error("TO: %r", to_emails)

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    logger.error("SMTP HOST=%s PORT=%s USER=%s", smtp_host, smtp_port, smtp_user)

    try:
        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.set_content(body)

        with open(attachment, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="octet-stream",
                filename=attachment.name,
            )

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.set_debuglevel(1)  # 🔥 ПЕЧАТАЕТ ВСЮ SMTP СЕССИЮ
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.error("SMTP SEND OK")

    except Exception as e:
        logger.exception("SMTP SEND FAILED")
        raise
