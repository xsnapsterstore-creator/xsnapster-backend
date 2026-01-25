from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.order import Payment
from services.razorpay_service import razorpay_service
from utils.payment_finalizer import finalize_razorpay_payment


def verify_payment_util(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    user_id: str,
    db: Session
):
    """
    Verify Razorpay payment signature (client-side confirmation).
    Final payment state is handled by shared finalizer.
    """

    # 1️⃣ Verify Razorpay signature
    if not razorpay_service.verify_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # 2️⃣ Fetch payment
    payment = (
        db.query(Payment)
        .filter(
            Payment.gateway_order_id == razorpay_order_id,
            Payment.payment_method == "RAZORPAY"
        )
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    # 3️⃣ Authorization check
    if payment.order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 4️⃣ Finalize safely (idempotent)
    finalized_payment = finalize_razorpay_payment(
        db=db,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        raw_response={
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
    )

    return {
        "status": "success",
        "message": "Payment verified",
        "order_id": finalized_payment.order_id,
        "payment_id": finalized_payment.id
    }
