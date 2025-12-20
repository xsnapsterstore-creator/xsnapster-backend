import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"



class Settings(BaseSettings):
    PROJECT_NAME: str
    DATABASE_URL: str
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: float
    REFRESH_TOKEN_EXPIRE_DAYS: float
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    SMTP_SERVER: str
    SMTP_PORT: int

    
    S3_BUCKET_NAME: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    SUPABASE_STORAGE_URL: str

    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str



    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()

