from utils.email import send_email, build_base_template, build_order_confirmation_template
from core.config import settings


def send_admin_order_notification(admin_email: str, from_email: str, order, invoice_bytes: bytes | None = None):
    """Send detailed order notification to admin with optional invoice attachment."""
    
    # Build items list for display
    items_html = ""
    for item in order.items:
        items_html += f"""
            <tr>
                <td style="padding:8px 0; border-bottom:1px solid #eee;">
                    {item.product.title} ({item.dimension}) × {item.quantity}
                </td>
                <td align="right" style="padding:8px 0; border-bottom:1px solid #eee;">
                    ₹{item.price * item.quantity:,.2f}
                </td>
            </tr>
        """

    subject = f"🛒 New Order #{order.id} - ₹{order.amount:,.2f}"

    content = f"""
        <div style="background:#f8f9fa; padding:20px; border-radius:8px; margin-bottom:20px;">
            <h2 style="margin:0 0 10px 0; color:#1a1a1a;">New Order Received</h2>
            <p style="margin:0; font-size:24px; font-weight:bold; color:#16a34a;">
                Order #{order.id}
            </p>
        </div>

        <h3 style="margin:20px 0 10px 0; color:#1a1a1a;">Customer Details</h3>
        <table cellpadding="0" cellspacing="0" border="0" style="font-size:14px;">
            <tr>
                <td style="padding:5px 20px 5px 0; color:#666;">Name:</td>
                <td style="padding:5px 0; font-weight:500;">{order.delivery_name}</td>
            </tr>
            <tr>
                <td style="padding:5px 20px 5px 0; color:#666;">Email:</td>
                <td style="padding:5px 0;">{order.user.email}</td>
            </tr>
            <tr>
                <td style="padding:5px 20px 5px 0; color:#666;">Phone:</td>
                <td style="padding:5px 0;">{order.delivery_phone_number}</td>
            </tr>
        </table>

        <h3 style="margin:25px 0 10px 0; color:#1a1a1a;">Shipping Address</h3>
        <p style="margin:0; font-size:14px; color:#666; line-height:1.6;">
            {order.delivery_address_line}<br/>
            {order.delivery_city}, {order.delivery_state} {order.delivery_zip_code}
        </p>

        <h3 style="margin:25px 0 10px 0; color:#1a1a1a;">Order Items</h3>
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="font-size:14px;">
            {items_html}
        </table>

        <h3 style="margin:25px 0 10px 0; color:#1a1a1a;">Payment Summary</h3>
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="font-size:14px; max-width:300px;">
            <tr>
                <td style="padding:5px 0; color:#666;">Subtotal:</td>
                <td align="right" style="padding:5px 0;">₹{order.items_subtotal:,.2f}</td>
            </tr>
            {"<tr><td style='padding:5px 0; color:#16a34a;'>Coupon (" + order.coupon_code + "):</td><td align='right' style='padding:5px 0; color:#16a34a;'>-₹" + f'{order.coupon_discount_amount:,.2f}' + "</td></tr>" if order.coupon_code else ""}
            <tr>
                <td style="padding:5px 0; color:#666;">Delivery:</td>
                <td align="right" style="padding:5px 0;">{"FREE" if order.delivery_charge == 0 else f"₹{order.delivery_charge:,.2f}"}</td>
            </tr>
            <tr>
                <td style="padding:10px 0; font-weight:bold; border-top:2px solid #1a1a1a;">Total:</td>
                <td align="right" style="padding:10px 0; font-weight:bold; font-size:18px; border-top:2px solid #1a1a1a;">
                    ₹{order.amount:,.2f}
                </td>
            </tr>
        </table>

        <div style="margin-top:25px; padding:15px; background:#f0f0f0; border-radius:6px;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="font-size:14px;">
                <tr>
                    <td style="color:#666;">Payment Method:</td>
                    <td align="right" style="font-weight:500;">{order.payment.payment_method if order.payment else 'N/A'}</td>
                </tr>
                <tr>
                    <td style="color:#666; padding-top:8px;">Status:</td>
                    <td align="right" style="padding-top:8px;">
                        <span style="background:#fef3c7; color:#b45309; padding:4px 10px; border-radius:4px; font-size:12px; font-weight:500;">
                            {order.order_status.value}
                        </span>
                    </td>
                </tr>
            </table>
        </div>
    """

    html_body = build_base_template("New Order Notification", content)

    text_body = f"""
    New Order Received

    Order ID: #{order.id}
    Customer: {order.delivery_name} ({order.user.email})
    Phone: {order.delivery_phone_number}
    
    Shipping Address:
    {order.delivery_address_line}
    {order.delivery_city}, {order.delivery_state} {order.delivery_zip_code}

    Subtotal: ₹{order.items_subtotal:,.2f}
    {"Coupon (" + order.coupon_code + "): -₹" + f'{order.coupon_discount_amount:,.2f}' if order.coupon_code else ""}
    Delivery: {"FREE" if order.delivery_charge == 0 else f"₹{order.delivery_charge:,.2f}"}
    Total: ₹{order.amount:,.2f}
    
    Payment: {order.payment.payment_method if order.payment else 'N/A'}
    Status: {order.order_status.value}
    """

    attachments = None
    if invoice_bytes:
        attachments = [
            {
                "filename": f"{order.invoice_number}.pdf",
                "content": invoice_bytes,
                "mime_type": "application/pdf"
            }
        ]

    send_email(admin_email, from_email, subject, html_body, text_body, attachments=attachments)


def send_order_confirmation_email(
    user_email: str,
    from_email: str,
    order,
    invoice_bytes: bytes | None = None
):
    """Send professional order confirmation email to customer."""
    
    # Build order items list using correct model fields
    order_items = []
    for item in order.items:
        order_items.append({
            "title": item.product.title,
            "dimension": item.dimension,
            "quantity": item.quantity,
            "price": item.price,
            "image": item.product.image_links[0] if item.product.image_links else None
        })
    
    # Build shipping address from order fields
    shipping_address = {
        "name": order.delivery_name,
        "address_line": order.delivery_address_line,
        "city": order.delivery_city,
        "state": order.delivery_state,
        "zip_code": order.delivery_zip_code,
        "phone": order.delivery_phone_number
    }
    
    # Payment method display
    payment_method = "Cash on Delivery" if order.payment and order.payment.payment_method == "COD" else "Prepaid (Online)"
    
    # Build view order URL using user ID
    view_order_url = f"https://www.xsnapster.store/user/{order.user.id}"

    subject = f"{order.delivery_name.split()[0]}, Your Order #{order.id} with XSNAPSTER is Confirmed!"

    html_body = build_order_confirmation_template(
        customer_name=order.delivery_name.split()[0],  # First name only
        order_id=order.id,
        order_items=order_items,
        items_subtotal=order.items_subtotal,
        coupon_code=order.coupon_code,
        coupon_discount=order.coupon_discount_amount or 0,
        delivery_charge=order.delivery_charge,
        total_amount=order.amount,
        shipping_address=shipping_address,
        payment_method=payment_method,
        view_order_url=view_order_url
    )

    # Plain text version
    items_text = "\n".join([
        f"  - {item['title']} ({item['dimension']}) × {item['quantity']} = ₹{item['price'] * item['quantity']:,.2f}"
        for item in order_items
    ])
    
    text_body = f"""
Order Confirmed! #{order.id}

Thank you {order.delivery_name.split()[0]}, we have received your order!

What happens next:
1. We'll pack your items within 12-24 hours
2. Our courier partners will pick up your order within 24-48 hours
3. You'll receive a tracking link via email & SMS once shipped

Order Summary:
{items_text}

Subtotal: ₹{order.items_subtotal:,.2f}
{"Discount (" + order.coupon_code + "): -₹" + f'{order.coupon_discount_amount:,.2f}' if order.coupon_code else ""}
Shipping: {"FREE" if order.delivery_charge == 0 else f"₹{order.delivery_charge:,.2f}"}
Total: ₹{order.amount:,.2f}

Shipping Address:
{order.delivery_name}
{order.delivery_address_line}
{order.delivery_city}, {order.delivery_state} {order.delivery_zip_code}
Phone: {order.delivery_phone_number}

Payment: {payment_method}

View your order: {view_order_url}

Thank you for shopping with XSNAPSTER!
    """

    attachments = None
    if invoice_bytes:
        attachments = [
            {
                "filename": f"{order.invoice_number}.pdf",
                "content": invoice_bytes,
                "mime_type": "application/pdf"
            }
        ]

    send_email(
        user_email,
        from_email,
        subject,
        html_body,
        text_body,
        attachments=attachments
    )


def send_otp_email(to_email: str, from_email: str, otp: str):
    """Send OTP verification email."""

    subject = "Your XSNAPSTER One-Time Password (OTP)"

    content = f"""
        <div style="text-align:center; padding:20px;">
            <h2 style="margin:0 0 20px 0; color:#1a1a1a;">Verify Your Email</h2>
            <p style="margin:0 0 30px 0; font-size:15px; color:#666666;">
                Use the OTP below to complete verification:
            </p>

            <div style="
                display:inline-block;
                margin:0 auto 30px auto;
                padding:20px 40px;
                background:linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                border-radius:8px;
                font-size:32px;
                letter-spacing:8px;
                font-weight:bold;
                color:#ffffff;
            ">
                {otp}
            </div>

            <p style="margin:0; font-size:14px; color:#888888;">
                This OTP is valid for <strong style="color:#1a1a1a;">5 minutes</strong>.
            </p>
            <p style="margin:15px 0 0 0; font-size:13px; color:#999999;">
                If you didn't request this, please ignore this email.
            </p>
        </div>
    """

    html_body = build_base_template("XSNAPSTER OTP", content)

    text_body = f"""
    Your XSNAPSTER OTP is: {otp}
    Valid for 5 minutes.
    
    If you didn't request this, please ignore this email.
    """

    send_email(to_email, from_email, subject, html_body, text_body)
