from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from email_validator import validate_email, EmailNotValidError
from core.config import settings





def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    attachments: list | None = None,
):
    """
    Generic email sender using SMTP SSL.

    attachments format:
    [
        {
            "filename": "invoice.pdf",
            "content": bytes,
            "mime_type": "application/pdf"
        }
    ]
    """

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_USER
    msg["To"] = to_email

    # Alternative body (text + html)
    body = MIMEMultipart("alternative")
    body.attach(MIMEText(text_body, "plain"))
    body.attach(MIMEText(html_body, "html"))

    msg.attach(body)

    # Attach files if provided
    if attachments:
        for attachment in attachments:

            part = MIMEApplication(
                attachment["content"],
                _subtype=attachment.get("mime_type", "octet-stream").split("/")[-1]
            )

            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=attachment["filename"],
            )

            msg.attach(part)

    try:
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, 465) as server:
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")
    
def build_base_template(title: str, content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f5f5f5; font-family:Arial, sans-serif;">

        <table width="100%" cellpadding="0" cellspacing="0" border="0" 
               style="background-color:#f5f5f5;">
            <tr>
                <td align="center">

                    <!-- Main Container -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="max-width:600px; background:#ffffff; border-radius:8px; overflow:hidden; margin:20px auto;">

                        <!-- Header -->
                        <tr>
                            <td align="center" style="padding:20px; background:#000000;">
                                <img 
                                    src="https://khnbsjuczeylcjrlrtni.supabase.co/storage/v1/object/public/xsnapster/logo/logo.png"
                                    alt="XSnapster"
                                    width="160"
                                    style="display:block; max-width:100%; height:auto;"
                                />
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td align="left" style="padding:30px; color:#333333;">
                                {content}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td align="center" style="padding:20px; background:#fafafa; font-size:12px; color:#999;">
                                © 2026 XSnapster. All rights reserved.<br/>
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

