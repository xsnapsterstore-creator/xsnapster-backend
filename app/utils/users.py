from sqlalchemy.orm import Session
from models.users import User, Address
from models.order import Order
from schemas.order import OrderSchema
def get_user_default_address(db: Session, user_id: str):
    """
    Returns the user's default address, or None if not set.
    """

    return (
        db.query(Address)
        .filter(Address.user_id == user_id, Address.is_default == True)
        .first()
    )

def get_user_orders(db: Session, user_id: str):
    """
    Returns all orders belonging to the user with computed totals.
    """

    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    order_schemas = []

    for order in orders:
        # Calculate totals
        total_items = sum(item.quantity for item in order.items)
        total_cost = sum(item.price * item.quantity for item in order.items)

        paid_amount = order.payment.amount if order.payment else None
        payment_method = "Razorpay" if order.payment else None

        # Get list of products in this order
        product_ids = [item.product_id for item in order.items]


        schema = OrderSchema(
            id=order.id,
            product_ids=product_ids,  # ← FIXED
            razorpay_order_id=order.razorpay_order_id,
            amount=order.amount,
            status=order.status.value if hasattr(order.status, "value") else order.status,
            created_at=order.created_at,

            total_items=total_items,
            total_cost=total_cost,

            payment=order.payment.status if order.payment else None,
            paid_amount=paid_amount,
            payment_method=payment_method,
        )

        order_schemas.append(schema)

    return order_schemas
