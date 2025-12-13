from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.order import Order, Payment
from services.razorpay_service import razorpay_service


def verify_payment_util(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    user_id: str,
    db: Session
):
    """
    Verify Razorpay payment signature and update Payment + Order
    """

    # 1️⃣ Verify Razorpay signature (SERVER SIDE ONLY)
    if not razorpay_service.verify_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # 2️⃣ Fetch Payment using Razorpay order_id
    payment = db.query(Payment).filter(
        Payment.gateway_order_id == razorpay_order_id,
        Payment.payment_method == "RAZORPAY"
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    # 3️⃣ Prevent double processing
    if payment.status == "SUCCESS":
        return {
            "status": "success",
            "message": "Payment already verified",
            "order_id": payment.order_id
        }

    # 4️⃣ Update payment record
    payment.transaction_id = razorpay_payment_id
    payment.signature = razorpay_signature
    payment.status = "SUCCESS"

    # (optional but recommended)
    payment.raw_response = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    }

    # 5️⃣ Update order status
    order = payment.order

    if order.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to verify this payment"
        )
    order.order_status = "CONFIRMED"

    db.commit()
    db.refresh(payment)
    db.refresh(order)

    return {
        "status": "success",
        "message": "Payment verified successfully",
        "order_id": order.id,
        "payment_id": payment.id
    }
