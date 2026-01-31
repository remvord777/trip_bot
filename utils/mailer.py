import smtplib
from email.message import EmailMessage
from pathlib import Path

/////12/////
SMTP_HOST = "lr600.intermatic.energy"
SMTP_PORT = 3587
SMTP_USER = "vorobev@intermatic.energy"
SMTP_PASSWORD = "76ex9*c24B"   # ⚠️ лучше потом вынести в config.py


def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    file_path: Path,
):
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
