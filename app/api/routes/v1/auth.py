from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.orm import Session
from db.session import get_db
from services.auth_service import request_otp, verify_otp_and_issue_tokens, refresh_tokens, logout_user
from schemas.auth import RequestOTP, OTPVerifyRequest, AuthResponse
from core.security import get_current_user
from models.users import User

router = APIRouter(prefix="/v1/auth", tags=["Auth"])
REFRESH_TOKEN_MAX_AGE = (6 * 24 + 23) * 60 * 60


# 1️⃣ Request OTP
@router.post("/request-otp")
def request_otp_route(payload: RequestOTP, db: Session = Depends(get_db)):
    print( "Requesting OTP for identifier:", payload.identifier)
    return request_otp(db, payload.identifier)


# 2️⃣ Verify OTP & login (issue tokens)
@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp_route(payload: OTPVerifyRequest, response: Response, db: Session = Depends(get_db)):
    access_token, refresh_token, user = verify_otp_and_issue_tokens(db, payload.identifier, payload.otp)

    # Set refresh token in HttpOnly cookie
    print("Setting refresh token cookie", refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        domain=".xsnapster.store",   # want subdomain sharing
        max_age=30 * 24 * 60 * 60,
        path="/"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "phone_number": user.phone_number,
        },
    }


# 3️⃣ Refresh tokens
@router.post("/refresh", response_model=AuthResponse)
def refresh_token_route(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        access_token, refresh_token, user = refresh_tokens(request, db)

    

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            domain=".xsnapster.store",
            max_age=REFRESH_TOKEN_MAX_AGE,
            path="/",
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
            },
        }

    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            response.delete_cookie(
                key="refresh_token",
                domain=".xsnapster.store",
                path="/",
                secure=True,
                samesite="none",
            )
        raise e


@router.post("/logout")
def logout_route(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("Logging out user:", current_user.id)
    return logout_user(response, db, current_user)


