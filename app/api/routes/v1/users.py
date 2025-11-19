from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from db.session import get_db
from core.security import get_current_user
from models.users import User


router = APIRouter(prefix="/v1/user", tags=["User"])

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }
