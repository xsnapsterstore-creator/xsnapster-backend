from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import json
from email_validator import validate_email, EmailNotValidError
from core.config import settings


def send_email(
    to_email: str,
    from_email: str,
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
    msg["From"] = from_email
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


def build_gmail_action_schema(order_id: int, view_url: str) -> str:
    """
    Build Gmail Action schema (JSON-LD) for 'View Order' button.
    This enables Gmail's smart action buttons in the inbox preview.
    """
    schema = {
        "@context": "http://schema.org",
        "@type": "EmailMessage",
        "potentialAction": {
            "@type": "ViewAction",
            "target": view_url,
            "name": "View Order"
        },
        "description": f"View your XSNAPSTER order #{order_id}"
    }
    return f'<script type="application/ld+json">{json.dumps(schema)}</script>'

    
def build_base_template(title: str, content: str, gmail_schema: str = "") -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="light">
        <meta name="supported-color-schemes" content="light">
        <title>{title}</title>
        {gmail_schema}
        <style>
            /* Force light mode in all email clients */
            :root {{
                color-scheme: light;
                supported-color-schemes: light;
            }}
            @media (prefers-color-scheme: dark) {{
                body, table, td, div, p, a, span, h1, h2, h3, h4, h5, h6 {{
                    background-color: #f5f5f5 !important;
                    color: #333333 !important;
                }}
                .email-container {{
                    background-color: #ffffff !important;
                }}
                .email-header {{
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
                }}
                .email-footer {{
                    background-color: #1a1a1a !important;
                }}
            }}
            /* Gmail dark mode fix */
            u + .body .email-container {{
                background-color: #ffffff !important;
            }}
            /* Outlook dark mode fix */
            [data-ogsc] .email-container {{
                background-color: #ffffff !important;
            }}
        </style>
        <!--[if mso]>
        <style type="text/css">
            body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
        </style>
        <![endif]-->
    </head>
    <body class="body" style="margin:0; padding:0; background-color:#f5f5f5 !important; font-family:'Segoe UI', Arial, sans-serif;">

        <table width="100%" cellpadding="0" cellspacing="0" border="0" 
               style="background-color:#f5f5f5 !important;">
            <tr>
                <td align="center">

                    <!-- Main Container -->
                    <table class="email-container" width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="max-width:600px; background-color:#ffffff !important; border-radius:8px; overflow:hidden; margin:20px auto; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">

                        <!-- Header -->
                        <tr>
                            <td class="email-header" align="center" style="padding:25px 20px; background:linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;">
                                <img 
                                    src="https://khnbsjuczeylcjrlrtni.supabase.co/storage/v1/object/public/xsnapster/logo/logo.png"
                                    alt="XSNAPSTER"
                                    width="180"
                                    style="display:block; max-width:100%; height:auto;"
                                />
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:0; color:#333333 !important; background-color:#ffffff !important;">
                                {content}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td class="email-footer" style="padding:30px 20px; background-color:#1a1a1a !important; text-align:center;">
                                <p style="margin:0 0 15px 0; font-size:13px; color:#888888 !important;">
                                    Have questions? We're here to help!
                                </p>
                                <p style="margin:0 0 15px 0;">
                                    <a href="mailto:support@xsnapster.store" style="color:#ffffff !important; text-decoration:none; font-size:14px;">
                                        support@xsnapster.store
                                    </a>
                                </p>
                                <p style="margin:0 0 20px 0;">
                                    <a href="https://www.instagram.com/xsnapster.store/" style="text-decoration:none;">
                                        <img src="https://cdn-icons-png.flaticon.com/512/174/174855.png" 
                                             alt="Instagram" width="28" height="28" 
                                             style="display:inline-block; vertical-align:middle;"/>
                                    </a>
                                </p>
                                <p style="margin:0; font-size:11px; color:#666666 !important;">
                                    © 2026 XSNAPSTER. All rights reserved.
                                </p>
                            </td>
                        </tr>

                    </table>

                </td>
            </tr>
        </table>

    </body>
    </html>
    """


def build_order_confirmation_template(
    customer_name: str,
    order_id: int,
    order_items: list,
    items_subtotal: float,
    coupon_code: str | None,
    coupon_discount: float,
    delivery_charge: float,
    total_amount: float,
    shipping_address: dict,
    payment_method: str,
    view_order_url: str
) -> str:
    """
    Build a professional order confirmation email template like GIVA.
    
    order_items format: [{"title": str, "dimension": str, "quantity": int, "price": float, "image": str | None}]
    shipping_address format: {"name": str, "address_line": str, "city": str, "state": str, "zip_code": str, "phone": str}
    """
    
    # Build order items HTML
    items_html = ""
    for item in order_items:
        item_image = item.get("image") or "https://via.placeholder.com/60x60?text=Product"
        items_html += f"""
        <tr>
            <td style="padding:15px 0; border-bottom:1px solid #f0f0f0; background-color:#fafafa !important;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td width="70" valign="top">
                            <img src="{item_image}" alt="{item['title']}" 
                                 width="60" height="60" 
                                 style="display:block; border-radius:6px; object-fit:cover;"/>
                        </td>
                        <td style="padding-left:15px;" valign="top">
                            <p style="margin:0 0 5px 0; font-weight:600; color:#1a1a1a !important; font-size:14px;">
                                {item['title']}
                            </p>
                            <p style="margin:0; font-size:12px; color:#666666 !important;">
                                {item.get('dimension', '')} × {item['quantity']}
                            </p>
                        </td>
                        <td align="right" valign="top" style="white-space:nowrap;">
                            <p style="margin:0; font-weight:600; color:#1a1a1a !important; font-size:14px;">
                                ₹{item['price'] * item['quantity']:,.2f}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """
    
    # Coupon discount row
    coupon_html = ""
    if coupon_code and coupon_discount > 0:
        coupon_html = f"""
        <tr>
            <td style="padding:8px 0; font-size:14px; color:#16a34a !important;">
                <span style="background:#dcfce7; padding:2px 8px; border-radius:4px; font-size:12px;">
                    {coupon_code}
                </span>
            </td>
            <td align="right" style="font-size:14px; color:#16a34a; font-weight:500;">
                -₹{coupon_discount:,.2f}
            </td>
        </tr>
        """
    
    # Delivery charge display
    delivery_display = "FREE" if delivery_charge == 0 else f"₹{delivery_charge:,.2f}"
    delivery_color = "#16a34a" if delivery_charge == 0 else "#333333"
    
    content = f"""
    <!-- Hero Section -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;">
        <tr>
            <td align="center" style="padding:40px 30px; background-color:#f8f9fa !important;">
                <div style="width:70px; height:70px; background-color:#16a34a !important; border-radius:50%; margin:0 auto 20px auto; text-align:center; line-height:70px;">
                    <span style="font-size:32px; color:#ffffff !important;">✓</span>
                </div>
                <h1 style="margin:0 0 10px 0; font-size:26px; font-weight:600; color:#1a1a1a !important;">
                    Order Confirmed!
                </h1>
                <p style="margin:0; font-size:15px; color:#666666 !important;">
                    Thank you <strong style="color:#1a1a1a !important;">{customer_name}</strong>, we have received your order 
                    <strong style="color:#1a1a1a !important;">#{order_id}</strong>
                </p>
            </td>
        </tr>
    </table>

    <!-- View Order Button -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff !important;">
        <tr>
            <td align="center" style="padding:25px 30px 15px 30px; background-color:#ffffff !important;">
                <a href="{view_order_url}" 
                   style="display:inline-block; padding:14px 40px; background-color:#1a1a1a !important; color:#ffffff !important; 
                          text-decoration:none; border-radius:6px; font-size:14px; font-weight:600;
                          box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                    View Order
                </a>
            </td>
        </tr>
    </table>

    <!-- What Happens Next -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff !important;">
        <tr>
            <td style="padding:20px 30px 30px 30px; background-color:#ffffff !important;">
                <h2 style="margin:0 0 20px 0; font-size:18px; font-weight:600; color:#1a1a1a !important;">
                    What happens next?
                </h2>
                
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td width="50" valign="top">
                            <div style="width:36px; height:36px; background-color:#f0f0f0 !important; border-radius:50%; 
                                        text-align:center; line-height:36px; font-size:16px;">📦</div>
                        </td>
                        <td style="padding-bottom:15px;">
                            <p style="margin:0; font-size:14px; color:#333333 !important; font-weight:500;">
                                Order Processing
                            </p>
                            <p style="margin:5px 0 0 0; font-size:13px; color:#666666 !important;">
                                We'll pack your items within 12-24 hours
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td width="50" valign="top">
                            <div style="width:36px; height:36px; background-color:#f0f0f0 !important; border-radius:50%; 
                                        text-align:center; line-height:36px; font-size:16px;">🚚</div>
                        </td>
                        <td style="padding-bottom:15px;">
                            <p style="margin:0; font-size:14px; color:#333333 !important; font-weight:500;">
                                Pickup & Dispatch
                            </p>
                            <p style="margin:5px 0 0 0; font-size:13px; color:#666666 !important;">
                                Our courier partners will pick up your order within 24-48 hours
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td width="50" valign="top">
                            <div style="width:36px; height:36px; background-color:#f0f0f0 !important; border-radius:50%; 
                                        text-align:center; line-height:36px; font-size:16px;">📍</div>
                        </td>
                        <td>
                            <p style="margin:0; font-size:14px; color:#333333 !important; font-weight:500;">
                                Track Your Order
                            </p>
                            <p style="margin:5px 0 0 0; font-size:13px; color:#666666 !important;">
                                You'll receive a tracking link via email & SMS once shipped
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- Order Summary -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#fafafa !important;">
        <tr>
            <td style="padding:25px 30px; background-color:#fafafa !important;">
                <h2 style="margin:0 0 20px 0; font-size:18px; font-weight:600; color:#1a1a1a !important;">
                    Order Summary
                </h2>
                
                <!-- Items -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    {items_html}
                </table>

                <!-- Pricing Breakdown -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:20px;">
                    <tr>
                        <td style="padding:8px 0; font-size:14px; color:#666666;">
                            Subtotal
                        </td>
                        <td align="right" style="font-size:14px; color:#333333;">
                            ₹{items_subtotal:,.2f}
                        </td>
                    </tr>
                    {coupon_html}
                    <tr>
                        <td style="padding:8px 0; font-size:14px; color:#666666;">
                            Shipping
                        </td>
                        <td align="right" style="font-size:14px; color:{delivery_color}; font-weight:500;">
                            {delivery_display}
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" style="padding:15px 0 0 0; border-top:2px solid #e0e0e0;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="font-size:16px; font-weight:700; color:#1a1a1a;">
                                        Total
                                    </td>
                                    <td align="right" style="font-size:18px; font-weight:700; color:#1a1a1a;">
                                        ₹{total_amount:,.2f}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- Shipping & Payment Info -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff !important;">
        <tr>
            <td style="padding:25px 30px; background-color:#ffffff !important;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td width="50%" valign="top" style="padding-right:15px;">
                            <h3 style="margin:0 0 12px 0; font-size:14px; font-weight:600; color:#1a1a1a !important; text-transform:uppercase; letter-spacing:0.5px;">
                                Shipping Address
                            </h3>
                            <p style="margin:0; font-size:13px; color:#666666 !important; line-height:1.6;">
                                {shipping_address['name']}<br/>
                                {shipping_address['address_line']}<br/>
                                {shipping_address['city']}, {shipping_address['state']} {shipping_address['zip_code']}<br/>
                                📞 {shipping_address['phone']}
                            </p>
                        </td>
                        <td width="50%" valign="top" style="padding-left:15px;">
                            <h3 style="margin:0 0 12px 0; font-size:14px; font-weight:600; color:#1a1a1a !important; text-transform:uppercase; letter-spacing:0.5px;">
                                Payment Method
                            </h3>
                            <p style="margin:0; font-size:13px; color:#666666 !important;">
                                {payment_method}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- Thank You Message -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f8f9fa !important;">
        <tr>
            <td align="center" style="padding:30px; background-color:#f8f9fa !important;">
                <p style="margin:0; font-size:15px; color:#666666 !important;">
                    We're honored to have you as part of the <strong style="color:#1a1a1a !important;">XSNAPSTER</strong> family! 🖤
                </p>
            </td>
        </tr>
    </table>
    """
    
    # Build Gmail action schema for View Order button
    gmail_schema = build_gmail_action_schema(order_id, view_order_url)
    
    return build_base_template("Order Confirmation", content, gmail_schema)