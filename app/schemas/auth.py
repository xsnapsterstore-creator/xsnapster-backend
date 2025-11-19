from pydantic import BaseModel, EmailStr, Field

class OTPVerifyRequest(BaseModel):
    identifier: str  # email or phone_number
    otp: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class RequestOTP(BaseModel):
    identifier: str  # can be email or phone number

class OTPVerifyRequest(BaseModel):
    identifier: str
    otp: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict