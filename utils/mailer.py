import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    attachment: Path,
):
    if not to_emails:
        raise RuntimeError("Список получателей пуст — письмо не отправлено")

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_user, smtp_pass]):
        raise RuntimeError("SMTP параметры не заданы в .env")

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
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
