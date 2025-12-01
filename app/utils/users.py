from sqlalchemy.orm import Session
from models.users import User, Address
from models.order import Order

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
    Returns all orders belonging to the user.
    """
    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
