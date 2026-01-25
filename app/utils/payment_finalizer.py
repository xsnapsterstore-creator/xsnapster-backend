from sqlalchemy.orm import Session
from models.order import Payment
from schemas.payment import PaymentStatus, OrderStatus


def finalize_razorpay_payment(
    *,
    db: Session,
    razorpay_order_id: str,
    razorpay_payment_id: str | None = None,
    raw_response: dict | None = None,
):
    payment = (
        db.query(Payment)
        .filter(
            Payment.gateway_order_id == razorpay_order_id,
            Payment.payment_method == "RAZORPAY"
        )
        .first()
    )

    if not payment:
        return None

    # 🔒 Idempotency guard
    if payment.status == PaymentStatus.SUCCESS:
        return payment

    payment.status = PaymentStatus.SUCCESS
    payment.transaction_id = razorpay_payment_id
    payment.raw_response = raw_response

    payment.order.order_status = OrderStatus.CONFIRMED

    db.commit()
    return payment
