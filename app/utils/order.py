# app/utils/payments.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.order import Order, Payment, OrderStatus
from models.products import Product
from services.razorpay_service import RazorpayService

razorpay = RazorpayService()

def create_order_util(product_id: int, db: Session):
    """Create a Razorpay order and store it in DB"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # create order in Razorpay
    order_data = razorpay.create_order(amount=product.price)

    order = Order(
        product_id=product.id,
        razorpay_order_id=order_data["id"],
        amount=product.price,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "order_id": order_data["id"],
        "razorpay_key": razorpay.key_id,
        "amount": product.price,
        "currency": "INR",
    }


def verify_payment_util(order_id: str, payment_id: str, signature: str, db: Session):
    """Verify payment signature and record payment"""

    if not razorpay.verify_signature(order_id, payment_id, signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    order = db.query(Order).filter(Order.razorpay_order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    existing_payment = db.query(Payment).filter(
        Payment.razorpay_payment_id == payment_id
    ).first()
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already processed")

    payment = Payment(
        order_id=order.id,
        razorpay_payment_id=payment_id,
        razorpay_signature=signature,
        amount=order.amount,
        status="paid",
    )

    order.status = OrderStatus.PAID
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "status": "success",
        "message": "Payment verified successfully!",
        "order_id": order.id,
        "payment_id": payment.id,
    }
