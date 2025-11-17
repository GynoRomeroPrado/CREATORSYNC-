"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.db.models import PlatformEnum, ContentTypeEnum, IncomeTypeEnum


# Creator Schemas
class CreatorBase(BaseModel):
    email: EmailStr
    full_name: str


class CreatorCreate(CreatorBase):
    pass


class CreatorResponse(CreatorBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Platform Connection Schemas
class PlatformConnectionBase(BaseModel):
    platform: PlatformEnum
    platform_user_id: str
    platform_username: str


class PlatformConnectionCreate(PlatformConnectionBase):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class PlatformConnectionResponse(PlatformConnectionBase):
    id: int
    creator_id: int
    is_active: bool
    connected_at: datetime
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


# Content Schemas
class ContentBase(BaseModel):
    platform_content_id: str
    content_type: ContentTypeEnum
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    published_at: datetime


class ContentCreate(ContentBase):
    platform_connection_id: int
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0


class ContentResponse(ContentBase):
    id: int
    creator_id: int
    platform_connection_id: int
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: Optional[float]
    created_at: datetime
    last_metrics_update: Optional[datetime]

    class Config:
        from_attributes = True


class ContentMetrics(BaseModel):
    """Aggregated content metrics."""
    total_views: int
    total_likes: int
    total_comments: int
    average_engagement_rate: float
    top_performing_content: List[ContentResponse]


# Income Schemas
class IncomeBase(BaseModel):
    amount: float = Field(gt=0, description="Income amount")
    currency: str = Field(default="USD", max_length=3)
    income_type: IncomeTypeEnum
    platform: PlatformEnum
    income_date: datetime


class IncomeCreate(IncomeBase):
    source_id: Optional[str] = None
    payer_name: Optional[str] = None
    description: Optional[str] = None


class IncomeResponse(IncomeBase):
    id: int
    creator_id: int
    payment_date: Optional[datetime]
    is_verified: bool
    is_reconciled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class IncomeStats(BaseModel):
    """Income statistics."""
    total_income: float
    income_by_platform: dict[str, float]
    income_by_type: dict[str, float]
    average_monthly_income: float
    growth_rate: float  # Percentage


# Attribution Schemas
class AttributionBase(BaseModel):
    income_id: int
    content_id: Optional[int] = None
    attributed_amount: float
    confidence_score: float = Field(ge=0.0, le=1.0)
    attribution_method: str


class AttributionCreate(AttributionBase):
    model_version: Optional[str] = None
    notes: Optional[str] = None


class AttributionResponse(AttributionBase):
    id: int
    creator_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AttributionResult(BaseModel):
    """Detailed attribution result linking content to income."""
    content: ContentResponse
    attributed_amount: float
    confidence_score: float
    percentage_of_total: float


# Forecast Schemas
class ForecastRequest(BaseModel):
    """Request for income forecast."""
    horizon_days: int = Field(default=90, ge=7, le=365)
    platform: Optional[PlatformEnum] = None
    income_type: Optional[IncomeTypeEnum] = None


class ForecastDataPoint(BaseModel):
    """Single forecast data point."""
    date: datetime
    predicted_income: float
    confidence_lower: float
    confidence_upper: float


class ForecastResponse(BaseModel):
    """Forecast response."""
    creator_id: int
    forecast_data: List[ForecastDataPoint]
    total_predicted_income: float
    model_version: str
    generated_at: datetime
    accuracy_metrics: Optional[dict] = None


# Dashboard Schemas
class DashboardOverview(BaseModel):
    """Complete dashboard overview."""
    creator: CreatorResponse
    total_income_30d: float
    total_income_90d: float
    income_forecast_30d: float
    content_metrics: ContentMetrics
    income_stats: IncomeStats
    recent_attributions: List[AttributionResult]
    top_earning_content: List[ContentResponse]


# Sync Schemas
class SyncRequest(BaseModel):
    """Request to sync data from a platform."""
    platform: PlatformEnum
    sync_content: bool = True
    sync_income: bool = True
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SyncStatus(BaseModel):
    """Status of sync operation."""
    platform: PlatformEnum
    status: str  # "pending", "in_progress", "completed", "failed"
    content_synced: int
    income_synced: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
