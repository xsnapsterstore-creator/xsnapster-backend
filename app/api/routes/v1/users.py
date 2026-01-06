from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from db.session import get_db
from core.security import get_current_user
from models.users import User
from schemas.users import UserProfileSchema
from utils.users import get_user_default_address, get_user_orders, get_user_orders_admin
from schemas.order import OrderSchema


router = APIRouter(prefix="/v1/user", tags=["User"])

@router.get("/profile", response_model=UserProfileSchema)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    default_address = get_user_default_address(db, current_user.id)

    return UserProfileSchema(
        id=current_user.id,
        email=current_user.email,
        phone_number=default_address.phone_number if default_address else None,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        default_address=default_address if default_address else None
    )


@router.get("/orders")
def get_user_orders_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = get_user_orders(db, current_user.id)
    return orders

@router.get("/orders/admin")
def get_all_user_orders_route(
    db: Session = Depends(get_db)
):
    orders = get_user_orders_admin(db)
    return orders