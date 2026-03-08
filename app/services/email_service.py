from utils.email import send_email, build_base_template



def send_admin_order_notification(admin_email: str, order):

    subject = f"New XSnapster Order Received - #{order.id}"

    content = f"""
        <h2>New Order Received</h2>

        <p><strong>Order ID:</strong> {order.id}</p>
        <p><strong>Customer:</strong> {order.user.email}</p>
        <p><strong>Total Amount:</strong> ${order.amount}</p>
        <p><strong>Status:</strong> {order.order_status}</p>
    """

    html_body = build_base_template("New Order Notification", content)

    text_body = f"""
    New Order Received

    Order ID: {order.id}
    Customer: {order.user.email}
    Total: ₹{order.amount}
    Status: {order.order_status}
    """

    send_email(admin_email, subject, html_body, text_body)




def send_order_confirmation_email(
    user_email: str,
    order,
    invoice_bytes: bytes | None = None
):

    subject = f"XSnapster Order Confirmation #{order.id}"

    content = f"""
        <h2>Thank You for Your Order 🎉</h2>

        <p>We’ve received your order successfully.</p>

        <p><strong>Order ID:</strong> {order.id}</p>
        <p><strong>Total Amount:</strong> ₹{order.amount}</p>

        <p>We’ll notify you once it’s processed.</p>
    """

    html_body = build_base_template("Order Confirmation", content)

    text_body = f"""
    Thank you for your order!

    Order ID: {order.id}
    Total: ₹{order.amount}
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
        subject,
        html_body,
        text_body,
        attachments=attachments
    )




def send_otp_email(to_email: str, otp: str):

    subject = "Your XSnapster One-Time Password (OTP)"

    content = f"""
        <h2>Verify Your Email</h2>
        <p>Use the OTP below to complete verification:</p>

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

        <p>This OTP is valid for <strong>5 minutes</strong>.</p>
    """

    html_body = build_base_template("XSnapster OTP", content)

    text_body = f"""
    Your XSnapster OTP is: {otp}
    Valid for 5 minutes.
    """

    send_email(to_email, subject, html_body, text_body)