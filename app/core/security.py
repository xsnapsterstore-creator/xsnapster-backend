import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status
from core.config import settings  
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.session import get_db
from models.users import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/verify-otp")

ALLOWED_EMAILS = {
    "divyanshi.gupta.twink15@gmail.com",
    "pixelavii007@gmail.com",
    "aryankannaujia@gmail.com",
    "md.aameen2710@gmail.com"
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    ttl = expires_delta or timedelta(
        minutes=float(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    expire = datetime.now(timezone.utc) + ttl

    to_encode.update({
        "exp": expire,
        "type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    ttl = expires_delta or timedelta(
        days=float(settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    expire = datetime.now(timezone.utc) + ttl

    to_encode.update({
        "exp": expire,
        "type": "refresh",
    })

    return jwt.encode(
        to_encode,
        settings.REFRESH_SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )




def verify_token(token: str, secret_key: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")




def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to authenticate a user via JWT bearer token.
    Returns the User object if valid, raises HTTPException otherwise.
    """
    try:
        payload = verify_token(token, settings.SECRET_KEY)
        user_id: str = payload.get("sub")  # "sub" is standard claim for user ID

        if payload.get("type") != "access":
            raise HTTPException(
                 status_code=status.HTTP_401_UNAUTHORIZED,
                 detail="Invalid access token",
                 headers={"WWW-Authenticate": "Bearer"},
               )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_with_email_check(
    current_user: User = Depends(get_current_user),
):
    """
    Wrapper dependency that allows access only to specific email IDs.
    """

    if current_user.email not in ALLOWED_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource",
        )

    return current_user