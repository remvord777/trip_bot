import os
import smtplib
import logging
from email.message import EmailMessage
from pathlib import Path   # ← ОБЯЗАТЕЛЬНО

logger = logging.getLogger(__name__)


def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    attachments: list[Path],
):
    logger.info("SMTP SEND START")
    logger.info("TO: %r", to_emails)

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_user, smtp_pass]):
        raise RuntimeError("SMTP env vars not set")

    try:
        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.set_content(body)

        for attachment in attachments:
            with open(attachment, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=attachment.name,
                )

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info("SMTP SEND OK")

    except Exception:
        logger.exception("SMTP SEND FAILED")
        raise
