from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import traceback
import logging

# Import your custom exceptions
from core.exceptions import (
    OTPAlreadySentException,
    OTPDeliveryFailedException,
    InvalidOTPException,
    DatabaseOperationException,
    LogoutFailedException,
    InvalidRefreshTokenException,
    TokenNotFoundException,
)

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    # --- OTP-related exceptions ---
    @app.exception_handler(OTPAlreadySentException)
    async def otp_already_sent_handler(request: Request, exc: OTPAlreadySentException):
        logger.info(f"OTPAlreadySentException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "OTP_ALREADY_SENT",
                "message": exc.detail,
            },
        )

    @app.exception_handler(OTPDeliveryFailedException)
    async def otp_delivery_failed_handler(request: Request, exc: OTPDeliveryFailedException):
        logger.error(f"OTPDeliveryFailedException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "OTP_DELIVERY_FAILED",
                "message": exc.detail,
            },
        )

    @app.exception_handler(InvalidOTPException)
    async def invalid_otp_handler(request: Request, exc: InvalidOTPException):
        logger.warning(f"InvalidOTPException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "INVALID_OTP",
                "message": exc.detail,
            },
        )

    # --- Database exceptions ---
    @app.exception_handler(DatabaseOperationException)
    async def database_operation_exception_handler(request: Request, exc: DatabaseOperationException):
        logger.error(f"DatabaseOperationException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "DATABASE_OPERATION_FAILED",
                "message": exc.detail,
            },
        )

    # --- Auth / Logout related exceptions ---
    @app.exception_handler(InvalidRefreshTokenException)
    async def invalid_refresh_token_handler(request: Request, exc: InvalidRefreshTokenException):
        logger.warning(f"InvalidRefreshTokenException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "INVALID_REFRESH_TOKEN",
                "message": exc.detail,
            },
        )

    @app.exception_handler(TokenNotFoundException)
    async def token_not_found_handler(request: Request, exc: TokenNotFoundException):
        logger.warning(f"TokenNotFoundException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "TOKEN_NOT_FOUND",
                "message": exc.detail,
            },
        )

    @app.exception_handler(LogoutFailedException)
    async def logout_failed_handler(request: Request, exc: LogoutFailedException):
        logger.error(f"LogoutFailedException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "LOGOUT_FAILED",
                "message": exc.detail,
            },
        )

    # --- Standard FastAPI HTTP exceptions ---
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTPException on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "HTTP_EXCEPTION",
                "message": exc.detail,
            },
        )

    # --- Fallback generic handler ---
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled error on {request.url.path}: {exc}\n{traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
