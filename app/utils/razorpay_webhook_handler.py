from sqlalchemy.orm import Session
from utils.payment_finalizer import finalize_razorpay_payment


def handle_razorpay_event(event: dict, db: Session):
    event_type = event.get("event")

    # We only care about final payment events
    if event_type != "payment.captured":
        return

    payment_entity = (
        event
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    razorpay_payment_id = payment_entity.get("id")
    razorpay_order_id = payment_entity.get("order_id")

    if not razorpay_order_id:
        return

    # ✅ SINGLE SOURCE OF TRUTH
    finalize_razorpay_payment(
        db=db,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        raw_response=event
    )
