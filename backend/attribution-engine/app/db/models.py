"""
Database models for the attribution engine.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, JSON, Text, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class PlatformEnum(str, enum.Enum):
    """Supported platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITCH = "twitch"
    PATREON = "patreon"


class ContentTypeEnum(str, enum.Enum):
    """Content types."""
    VIDEO = "video"
    SHORT = "short"
    LIVESTREAM = "livestream"
    POST = "post"
    STORY = "story"


class IncomeTypeEnum(str, enum.Enum):
    """Income types."""
    AD_REVENUE = "ad_revenue"
    BRAND_DEAL = "brand_deal"
    MEMBERSHIP = "membership"
    DONATION = "donation"
    AFFILIATE = "affiliate"
    OTHER = "other"


class Creator(Base):
    """Creator/User model."""
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    platforms = relationship("PlatformConnection", back_populates="creator")
    content = relationship("Content", back_populates="creator")
    income = relationship("Income", back_populates="creator")
    attributions = relationship("Attribution", back_populates="creator")


class PlatformConnection(Base):
    """Platform connection credentials."""
    __tablename__ = "platform_connections"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    platform = Column(SQLEnum(PlatformEnum), nullable=False)
    platform_user_id = Column(String, nullable=False)  # Platform's user ID
    platform_username = Column(String, nullable=False)
    access_token = Column(Text, nullable=True)  # Encrypted in production
    refresh_token = Column(Text, nullable=True)  # Encrypted in production
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default={})  # Additional platform-specific data

    # Relationships
    creator = relationship("Creator", back_populates="platforms")
    content = relationship("Content", back_populates="platform_connection")

    __table_args__ = (
        Index('ix_platform_creator', 'creator_id', 'platform'),
    )


class Content(Base):
    """Content items (videos, posts, streams, etc.)."""
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    platform_connection_id = Column(Integer, ForeignKey("platform_connections.id"), nullable=False)

    # Content identification
    platform_content_id = Column(String, nullable=False)  # Platform's content ID
    content_type = Column(SQLEnum(ContentTypeEnum), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)

    # Metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    watch_time_minutes = Column(Integer, nullable=True)  # For videos
    engagement_rate = Column(Float, nullable=True)

    # Timestamps
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_metrics_update = Column(DateTime, nullable=True)

    # Additional metadata
    metadata = Column(JSON, default={})  # Tags, categories, etc.

    # Relationships
    creator = relationship("Creator", back_populates="content")
    platform_connection = relationship("PlatformConnection", back_populates="content")
    attributions = relationship("Attribution", back_populates="content")

    __table_args__ = (
        Index('ix_content_platform_id', 'platform_connection_id', 'platform_content_id'),
        Index('ix_content_published', 'creator_id', 'published_at'),
    )


class Income(Base):
    """Income records from various sources."""
    __tablename__ = "income"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)

    # Income details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    income_type = Column(SQLEnum(IncomeTypeEnum), nullable=False)
    platform = Column(SQLEnum(PlatformEnum), nullable=False)

    # Source tracking
    source_id = Column(String, nullable=True)  # Platform's transaction/payment ID
    payer_name = Column(String, nullable=True)  # Brand name for brand deals

    # Time period
    income_date = Column(DateTime, nullable=False)  # When income was earned
    payment_date = Column(DateTime, nullable=True)  # When payment was received
    period_start = Column(DateTime, nullable=True)  # For recurring income
    period_end = Column(DateTime, nullable=True)

    # Status
    is_verified = Column(Boolean, default=False)
    is_reconciled = Column(Boolean, default=False)

    # Metadata
    description = Column(Text, nullable=True)
    metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("Creator", back_populates="income")
    attributions = relationship("Attribution", back_populates="income")

    __table_args__ = (
        Index('ix_income_creator_date', 'creator_id', 'income_date'),
    )


class Attribution(Base):
    """Attribution linking income to specific content."""
    __tablename__ = "attributions"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    income_id = Column(Integer, ForeignKey("income.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=True)

    # Attribution details
    attributed_amount = Column(Float, nullable=False)  # Portion of income
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    attribution_method = Column(String, nullable=False)  # "ml_model", "direct", "manual"

    # Model info
    model_version = Column(String, nullable=True)
    model_features = Column(JSON, nullable=True)  # Features used for attribution

    # Metadata
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("Creator", back_populates="attributions")
    income = relationship("Income", back_populates="attributions")
    content = relationship("Content", back_populates="attributions")

    __table_args__ = (
        Index('ix_attribution_income', 'income_id'),
        Index('ix_attribution_content', 'content_id'),
    )


class ForecastData(Base):
    """Income forecast data."""
    __tablename__ = "forecast_data"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)

    # Forecast details
    forecast_date = Column(DateTime, nullable=False)  # Date being forecasted
    predicted_income = Column(Float, nullable=False)
    confidence_lower = Column(Float, nullable=False)  # Lower bound
    confidence_upper = Column(Float, nullable=False)  # Upper bound

    # Model info
    model_version = Column(String, nullable=False)
    platform = Column(SQLEnum(PlatformEnum), nullable=True)  # If platform-specific
    income_type = Column(SQLEnum(IncomeTypeEnum), nullable=True)

    # Metadata
    features_used = Column(JSON, nullable=True)
    accuracy_metrics = Column(JSON, nullable=True)

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_forecast_creator_date', 'creator_id', 'forecast_date'),
    )
