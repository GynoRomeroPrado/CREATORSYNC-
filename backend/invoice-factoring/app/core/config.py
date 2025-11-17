"""
Application configuration for Invoice Factoring.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Invoice Factoring settings."""

    # App
    APP_NAME: str = "CreatorSync Invoice Factoring"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://creatorsync:creatorsync_dev_password@localhost:5432/creatorsync"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/3"

    # Stripe (for payments)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Plaid (for bank verification)
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    PLAID_ENV: str = "sandbox"

    # KYC/AML
    JUMIO_API_TOKEN: Optional[str] = None
    JUMIO_API_SECRET: Optional[str] = None

    # Factoring Configuration
    MIN_INVOICE_AMOUNT: float = 500.0  # Minimum $500
    MAX_INVOICE_AMOUNT: float = 100000.0  # Maximum $100k
    MIN_ADVANCE_RATE: float = 0.80  # 80%
    MAX_ADVANCE_RATE: float = 0.95  # 95%
    DEFAULT_FACTOR_RATE: float = 0.03  # 3% per 30 days
    DEFAULT_DUE_DAYS: int = 30

    # Risk Assessment
    MIN_RISK_SCORE: int = 60  # Minimum score to approve
    HIGH_RISK_THRESHOLD: int = 70
    LOW_RISK_THRESHOLD: int = 85

    # ML Models
    MODEL_PATH: str = "./ml-models/factoring"
    RISK_MODEL_VERSION: str = "v1.0"

    # Banking
    BANK_ACCOUNT_NUMBER: Optional[str] = None
    BANK_ROUTING_NUMBER: Optional[str] = None

    # Collections
    COLLECTION_REMINDER_DAYS: list[int] = [7, 3, 1]  # Days before due date
    LATE_FEE_RATE: float = 0.015  # 1.5% per month

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/3"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/3"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
