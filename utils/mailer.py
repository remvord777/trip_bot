import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

# ─────────────────────
# ЗАГРУЗКА ENV
# ─────────────────────
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

EMAIL_SIGNATURE = os.getenv("EMAIL_SIGNATURE", "").replace("\\n", "\n")


# ─────────────────────
# ВНУТРЕННЯЯ ФУНКЦИЯ
# ─────────────────────
def _apply_signature(body: str) -> str:
    if EMAIL_SIGNATURE:
        return f"{body}\n\n{EMAIL_SIGNATURE}"
    return body


# ─────────────────────
# ОДНО ВЛОЖЕНИЕ
# ─────────────────────
def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    file_path: Path,
):
    body = _apply_signature(body)

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with open(file_path, "rb") as f:
        file_data = f.read()

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=file_path.name,
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


# ─────────────────────
# НЕСКОЛЬКО ВЛОЖЕНИЙ
# ─────────────────────
def send_email_with_attachments(
    to_email: str,
    subject: str,
    body: str,
    file_paths: list[Path],
):
    body = _apply_signature(body)

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    for file_path in file_paths:
        with open(file_path, "rb") as f:
            file_data = f.read()

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file_path.name,
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
