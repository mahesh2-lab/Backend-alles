import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tenacity import retry, wait_exponential, stop_after_attempt
import os
import resend
from dotenv import load_dotenv
from .mail_content import generate_mail_content

load_dotenv()

resend.api_key = os.environ["RESEND_API_KEY"]


@retry(wait=wait_exponential(multiplier=2, min=2, max=30), stop=stop_after_attempt(5))
def send_email(to_email: str, candidate_name: str, position: str, is_eligible: bool, id: str, password: str):
    """Send email with retry logic."""

    print(
        f"📧 Sending email to {to_email} for position {position}, eligible: {is_eligible}, {candidate_name}"
    )
    content = generate_mail_content(candidate_name, position, is_eligible, id, password)
    body = content["html_content"]
    subject = content["subject"]

    params: resend.Emails.SendParams = {
        "from": "Acme <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": body,
    }

    email = resend.Emails.send(params)
    return email
