from sqlalchemy.orm import Session
from models.users import User, Address
from models.order import Order
from schemas.order import OrderSchema, OrderItemSchema
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
    Returns all orders belonging to the user with full product details.
    """

    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    order_list = []

    for order in orders:

        items_data = []

        for item in order.items:
            product = item.product

            items_data.append({
                "product_id": product.id,
                "title": product.title,
                "image": product.image_links[0] if product.image_links else None,
                "ordered_dimension": item.dimension,
                "ordered_price": item.price,
                "category": product.category_rel.name if product.category_rel else None,
                "subcategory": product.subcategory_rel.name if product.subcategory_rel else None,
                "quantity": 1,
            })

        print("this is item data", items_data)

        order_list.append({
            "id": order.id,
            "razorpay_order_id": order.razorpay_order_id,
            "amount": order.amount,
            "status": order.status.value if hasattr(order.status, "value") else order.status,
            "created_at": order.created_at, # totals
            "total_items": sum(i.quantity for i in order.items),
            "total_cost": sum(i.price * i.quantity for i in order.items),

            # payment
            "payment": order.payment.status if order.payment else None,
            "paid_amount": order.payment.amount if order.payment else None,
            "payment_method": "Razorpay" if order.payment else None,

            # the detailed product list
            "items": items_data
        })


    return order_list
