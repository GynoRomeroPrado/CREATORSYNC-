"""
Application configuration for Tax Optimizer.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Tax Optimizer settings."""

    # App
    APP_NAME: str = "CreatorSync Tax Optimizer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://creatorsync:creatorsync_dev_password@localhost:5432/creatorsync"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"  # Use DB 1 for tax optimizer

    # Plaid (Banking Integration)
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    PLAID_ENV: str = "sandbox"  # sandbox, development, production

    # AWS (for Textract - alternative to Tesseract)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    USE_AWS_TEXTRACT: bool = False  # Set to True to use AWS instead of Tesseract

    # OCR Configuration
    OCR_CONFIDENCE_THRESHOLD: float = 0.7
    OCR_MAX_FILE_SIZE_MB: int = 10

    # ML Models
    MODEL_PATH: str = "./ml-models/tax"
    CATEGORIZER_MODEL_VERSION: str = "v1.0"

    # Tax Configuration
    TAX_YEAR: int = 2024
    DEFAULT_TAX_BRACKET: float = 0.24  # 24%
    SELF_EMPLOYMENT_TAX_RATE: float = 0.153  # 15.3%
    HOME_OFFICE_DEDUCTION_METHOD: str = "simplified"  # "simplified" or "actual"

    # File Storage
    UPLOAD_DIR: str = "./uploads/receipts"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
