from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from models.users import User
from models.users import OTP
from models.refresh_token import RefreshToken
from core.security import create_access_token, create_refresh_token, verify_token
from utils.otp_sender import send_otp_email, validate_email
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import SQLAlchemyError
from core.exceptions import (
    OTPAlreadySentException,
    OTPDeliveryFailedException,
    DatabaseOperationException,
    InvalidOTPException,
    LogoutFailedException,
    InvalidRefreshTokenException,
    TokenNotFoundException,
)
import uuid
from core.config import settings


def request_otp(db, identifier: str):
    """
    Generates or reuses OTP for existing/new user.
    Prevents multiple active OTPs from being generated too frequently.
    """
    try:
        user = db.query(User).filter(
            (User.email == identifier) | (User.phone_number == identifier)
        ).first()

        if "@" in identifier:
            try:
               response = validate_email(identifier, check_deliverability=True)
               print("Email validation response:", response)
            except EmailNotValidError as e:
               raise HTTPException(status_code=400, detail=f"Invalid or undeliverable email: {str(e)}")

        new_user_created = False
        if not user:
            user = User(
                email=identifier if "@" in identifier else None,
                phone_number=None if "@" in identifier else identifier,
            )
            try:
                db.add(user)
                db.commit()
                db.refresh(user)
                new_user_created = True
            except SQLAlchemyError:
                db.rollback()
                raise DatabaseOperationException()

        existing_otp = (
            db.query(OTP)
            .filter(
                OTP.user_id == user.id,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow(),
            )
            .order_by(OTP.created_at.desc())
            .first()
        )

        if existing_otp:
            time_remaining = (existing_otp.expires_at - datetime.now(timezone.utc)).seconds
            raise OTPAlreadySentException(wait_seconds=time_remaining)

        otp_code = str(uuid.uuid4().int)[:6]
        otp = OTP(
            user_id=user.id,
            otp_code=otp_code,
            for_field="email" if user.email else "phone",
            expires_at=OTP.create_expiry(5),
        )

        try:
            db.add(otp)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise DatabaseOperationException()

        try:
            if user.email:
                send_otp_email(user.email, otp_code)
            elif user.phone_number:
                send_otp_sms(user.phone_number, otp_code)
        except Exception as e:
            db.rollback()
            raise OTPDeliveryFailedException(reason=str(e))

        msg = "Account created. OTP sent." if new_user_created else "Login OTP sent."
        return {"message": msg}

    except (OTPAlreadySentException, OTPDeliveryFailedException, DatabaseOperationException):
        raise
    except Exception:
        db.rollback()
        raise


# ----------------------------------------
# OTP VERIFICATION (already implemented)
# ----------------------------------------
def verify_otp_and_issue_tokens(db: Session, identifier: str, otp_code: str):
    """
    Verify OTP and issue access and refresh tokens.
    Reuses an existing refresh token if it exists and is still valid.
    """
    try:
        # --- find user ---
        user = db.query(User).filter(
            (User.email == identifier) | (User.phone_number == identifier)
        ).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        # --- verify OTP ---
        otp = (
            db.query(OTP)
            .filter(
                OTP.user_id == user.id,
                OTP.otp_code == otp_code,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow(),
            )
            .order_by(OTP.created_at.desc())
            .first()
        )
        if not otp:
            raise InvalidOTPException()

        print(f"OTP verified for user -2: {user.id}")

        otp.is_used = True
        user.is_verified = True

        # --- check for existing valid refresh token ---
        existing_refresh = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow(),
            )
            .order_by(RefreshToken.expires_at.desc())
            .first()
        )
        print(f"Existing refresh token: {existing_refresh}")

        if existing_refresh:
            refresh_token_str = existing_refresh.token
        else:
            refresh_token_str = create_refresh_token({"sub": user.id})
            new_refresh = RefreshToken(
                user_id=user.id,
                token=refresh_token_str,
                expires_at=RefreshToken.expiry(),
                is_revoked=False,
            )
            db.add(new_refresh)

        # --- generate access token ---
        access_token = create_access_token({"sub": user.id})

        # --- commit changes ---
        try:
            db.add_all([otp, user])  # refresh token already added if new
            db.commit()
        except Exception:
            db.rollback()
            raise DatabaseOperationException()

        return access_token, refresh_token_str, user

    except (
        OTPAlreadySentException,
        OTPDeliveryFailedException,
        InvalidOTPException,
        DatabaseOperationException,
    ):
        # re-raise known custom exceptions to be handled by global handler
        raise
    except Exception:
        # rollback and bubble up unexpected errors to global handler
        db.rollback()
        raise


# ----------------------------------------
# REFRESH TOKEN HANDLER
# ----------------------------------------
def refresh_tokens(request: Request, db: Session):
    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    # Verify token
    payload = verify_token(refresh_token_cookie, secret_key=settings.REFRESH_SECRET_KEY)
    user_id = payload.get("sub")

    # Validate refresh token in DB
    token_in_db = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token_cookie,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow(),
    ).first()
    if not token_in_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Issue new access token
    new_access = create_access_token({"sub": user.id})

    # Revoke old refresh token and create a new one
    token_in_db.is_revoked = True
    new_refresh = create_refresh_token({"sub": user.id})
    new_token = RefreshToken(
        user_id=user.id,
        token=new_refresh,
        expires_at=RefreshToken.expiry(),
    )

    try:
        db.add_all([token_in_db, new_token])
        db.commit()
    except Exception:
        db.rollback()
        raise DatabaseOperationException()

    return new_access, new_refresh, user

from fastapi import Request, Response
from sqlalchemy.orm import Session
from models.users import User
from models.refresh_token import RefreshToken
from core.exceptions import (
    LogoutFailedException,
    TokenNotFoundException,
)
from core.security import get_current_user

def logout_user(response: Response, db: Session, current_user: User):
    """
    Helper function to log out the current user by revoking all refresh tokens.
    """

    try:
        # Fetch all active refresh tokens for the user
        active_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        ).all()

        if not active_tokens:
            raise TokenNotFoundException()

        # Revoke all tokens
        for token in active_tokens:
            token.is_revoked = True
            db.add(token)
        db.commit()

        # Clear refresh token cookie
        response.delete_cookie("refresh_token")

        return {"success": True, "message": "User logged out successfully."}

    except TokenNotFoundException:
        raise  # propagate known exception for FastAPI handler

    except Exception as e:
        db.rollback()
        print(f"Logout failed: {e}")
        raise LogoutFailedException()
