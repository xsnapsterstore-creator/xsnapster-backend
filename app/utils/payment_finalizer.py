from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.order import Payment
from schemas.payment import PaymentStatus, OrderStatus


def compute_expected_order_total(order) -> float:
    """
    Compute the canonical payable total from persisted order snapshot.
    Uses post-coupon subtotal when available and supports legacy rows.
    """
    items_subtotal = float(order.items_subtotal or 0.0)
    coupon_discount = float(order.coupon_discount_amount or 0.0)

    if order.subtotal_after_coupon is not None:
        payable_items_subtotal = float(order.subtotal_after_coupon)
    elif coupon_discount > 0:
        payable_items_subtotal = max(items_subtotal - coupon_discount, 0.0)
    else:
        payable_items_subtotal = items_subtotal

    delivery_charge = float(order.delivery_charge or 0.0)
    return round(payable_items_subtotal + delivery_charge, 2)


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
        .with_for_update()
        .first()
    )

    if not payment:
        return None

    expected_total = compute_expected_order_total(payment.order)

    if round(float(payment.order.amount), 2) != expected_total:
        raise HTTPException(status_code=409, detail="Order amount breakdown mismatch")

    if round(float(payment.amount), 2) != expected_total:
        raise HTTPException(status_code=409, detail="Payment amount mismatch")

    # 🔒 Idempotency guard
    if payment.status == PaymentStatus.SUCCESS:
        return payment

    payment.status = PaymentStatus.SUCCESS
    payment.transaction_id = razorpay_payment_id
    payment.raw_response = raw_response

    payment.order.order_status = OrderStatus.CONFIRMED

    db.commit()
    from tasks.process_order import process_confirmed_order
    from tasks.notify_admin import notify_admin
    from tasks.shiprocket_order import create_shiprocket_order
    process_confirmed_order.send(payment.order_id)
    notify_admin.send(payment.order_id)
    create_shiprocket_order.send(payment.order_id)
    return payment
