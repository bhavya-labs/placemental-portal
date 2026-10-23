import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for resolving .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Placement Intelligence Platform"
    SECRET_KEY: str = "7cf8a569cb23dbbc8d48093db5f86cf574218ea1b0722e1b12b509ef4881fa2c"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = "sqlite:///./placement_portal.db"

    # CORS Allowed Origins (comma-separated list for Vite dev and production)
    FRONTEND_ORIGIN: str = "http://localhost:5173,http://127.0.0.1:5173,https://bhavya-labs.github.io"

    # Login Rate Limiting (Phase 1 Security Hardening)
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    LOGIN_RATE_LIMIT_WINDOW_MINUTES: int = 15

    # Parent Portal OTP and SMS Rate Limiting Config
    OTP_EXPIRY_MINUTES: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_REQUESTS_PER_WINDOW: int = 5
    OTP_RATE_LIMIT_WINDOW_HOURS: int = 1
    OTP_MAX_VERIFY_ATTEMPTS: int = 3
    SMS_ENV: str = "dev"

    # Database Seeding Controls (Must be explicitly opted-in; defaults to disabled for safety)
    ENABLE_DEMO_SEEDING: bool = False

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
