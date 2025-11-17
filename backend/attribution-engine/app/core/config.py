"""
Application configuration using Pydantic Settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "CreatorSync Attribution Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://creatorsync:creatorsync_dev_password@localhost:5432/creatorsync"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9093"
    KAFKA_TOPIC_INCOME: str = "income-events"
    KAFKA_TOPIC_CONTENT: str = "content-events"
    KAFKA_TOPIC_ANALYTICS: str = "analytics-events"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # Platform API Keys (stored securely in production)
    YOUTUBE_API_KEY: Optional[str] = None
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None
    INSTAGRAM_CLIENT_ID: Optional[str] = None
    INSTAGRAM_CLIENT_SECRET: Optional[str] = None
    TWITCH_CLIENT_ID: Optional[str] = None
    TWITCH_CLIENT_SECRET: Optional[str] = None
    PATREON_CLIENT_ID: Optional[str] = None
    PATREON_CLIENT_SECRET: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_YOUTUBE: int = 10000  # per day
    RATE_LIMIT_TIKTOK: int = 1000    # per day
    RATE_LIMIT_INSTAGRAM: int = 200  # per hour
    RATE_LIMIT_TWITCH: int = 800     # per minute
    RATE_LIMIT_PATREON: int = 500    # per hour

    # ML Models
    MODEL_PATH: str = "./ml-models"
    ATTRIBUTION_MODEL_VERSION: str = "v1.0"
    FORECAST_HORIZON_DAYS: int = 90  # 3 months

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
