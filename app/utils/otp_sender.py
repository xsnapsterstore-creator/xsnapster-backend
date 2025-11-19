import smtplib
from email.mime.text import MIMEText
from random import randint
from core.config import settings  



def send_otp_email(to_email: str, otp: str):
    """
    Send OTP via SMTP using contact@xsnapster.store
    """
    print("Sending OTP email to", to_email)
    subject = "Your XSnapster OTP Code"
    body = f"Your OTP is: {otp}. It will expire in 5 minutes."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = settings.EMAIL_USER  # contact@xsnapster.store
    msg['To'] = to_email

    try:
        print("Connecting to SMTP server")
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, 465) as server:
            # server.starttls()
            print("Logging in to SMTP server")
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            print("Sending email")
            response = server.send_message(msg)
            print("SMTP response:", response)
            print("OTP email sent successfully")
    except Exception as e:
        print("Error sending email:", e)
        raise
