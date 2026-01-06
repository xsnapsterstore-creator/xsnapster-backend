import smtplib
from email.mime.text import MIMEText
from random import randint
from core.config import settings  
from email_validator import validate_email, EmailNotValidError


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def send_otp_email(to_email: str, otp: str):
    """
    Send branded OTP email via SMTP using contact@xsnapster.store
    """

    subject = "Your XSnapster One-Time Password (OTP)"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>XSnapster OTP</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f5f5f5; font-family:Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center" style="padding:30px 0;">
                    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:8px; overflow:hidden;">
                        
                        <!-- Header -->
                        <tr>
                            <td align="center" style="padding:20px; background:#000000;">
                                <img 
                                    src="https://khnbsjuczeylcjrlrtni.supabase.co/storage/v1/object/public/xsnapster/logo/logo.png"
                                    alt="XSnapster"
                                    width="160"
                                    style="display:block;"
                                />
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:30px; color:#333333;">
                                <h2 style="margin-top:0;">Verify Your Email</h2>

                                <p>
                                    Thank you for choosing <strong>XSnapster</strong>.
                                    Use the One-Time Password (OTP) below to complete your verification.
                                </p>

                                <div style="
                                    margin:30px 0;
                                    padding:15px;
                                    text-align:center;
                                    background:#f0f0f0;
                                    border-radius:6px;
                                    font-size:28px;
                                    letter-spacing:4px;
                                    font-weight:bold;
                                ">
                                    {otp}
                                </div>

                                <p>
                                    This OTP is valid for <strong>5 minutes</strong>.
                                    Please do not share this code with anyone.
                                </p>

                                <p style="font-size:14px; color:#777;">
                                    If you did not request this code, please ignore this email.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td align="center" style="padding:20px; background:#fafafa; font-size:12px; color:#999;">
                                © {2026} XSnapster. All rights reserved.<br/>
                                Need help? Contact us at 
                                <a href="mailto:support@xsnapster.store" style="color:#999;">support@xsnapster.store</a>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_USER  # contact@xsnapster.store
    msg["To"] = to_email

    # Plain text fallback (IMPORTANT for deliverability)
    text_body = f"""
    Your XSnapster OTP is: {otp}

    This code is valid for 5 minutes.
    Do not share this OTP with anyone.

    If you did not request this, please ignore this email.
    """

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, 465) as server:
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        raise RuntimeError(f"Failed to send OTP email: {e}")


def validate_real_email(email: str):
    try:
        validated = validate_email(email, check_deliverability=True)
        return validated.email
    except EmailNotValidError as e:
        raise ValueError(str(e))