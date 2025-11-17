"""
API route definitions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.base import get_db
from app.db.models import Creator, Content, Income, Attribution, ForecastData, PlatformEnum
from app.api.schemas import (
    CreatorCreate, CreatorResponse,
    ContentCreate, ContentResponse, ContentMetrics,
    IncomeCreate, IncomeResponse, IncomeStats,
    AttributionCreate, AttributionResponse, AttributionResult,
    ForecastRequest, ForecastResponse,
    DashboardOverview,
    SyncRequest, SyncStatus
)
from app.services.attribution_service import AttributionService
from app.services.forecast_service import ForecastService
from app.tasks.sync_tasks import sync_platform_data

# Routers
creator_router = APIRouter()
content_router = APIRouter()
income_router = APIRouter()
attribution_router = APIRouter()
forecast_router = APIRouter()
dashboard_router = APIRouter()
sync_router = APIRouter()


# ============================================================================
# CREATOR ROUTES
# ============================================================================

@creator_router.post("/", response_model=CreatorResponse)
async def create_creator(creator: CreatorCreate, db: Session = Depends(get_db)):
    """Create a new creator."""
    db_creator = Creator(
        email=creator.email,
        full_name=creator.full_name
    )
    db.add(db_creator)
    db.commit()
    db.refresh(db_creator)
    return db_creator


@creator_router.get("/{creator_id}", response_model=CreatorResponse)
async def get_creator(creator_id: int, db: Session = Depends(get_db)):
    """Get creator by ID."""
    creator = db.query(Creator).filter(Creator.id == creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    return creator


@creator_router.get("/", response_model=List[CreatorResponse])
async def list_creators(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all creators."""
    creators = db.query(Creator).offset(skip).limit(limit).all()
    return creators


# ============================================================================
# CONTENT ROUTES
# ============================================================================

@content_router.post("/", response_model=ContentResponse)
async def create_content(content: ContentCreate, db: Session = Depends(get_db)):
    """Create a new content item."""
    # Get creator_id from platform_connection
    from app.db.models import PlatformConnection
    connection = db.query(PlatformConnection).filter(
        PlatformConnection.id == content.platform_connection_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Platform connection not found")

    db_content = Content(
        creator_id=connection.creator_id,
        **content.model_dump()
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


@content_router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, db: Session = Depends(get_db)):
    """Get content by ID."""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@content_router.get("/creator/{creator_id}", response_model=List[ContentResponse])
async def list_creator_content(
    creator_id: int,
    platform: Optional[PlatformEnum] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List content for a creator."""
    query = db.query(Content).filter(Content.creator_id == creator_id)

    if platform:
        from app.db.models import PlatformConnection
        query = query.join(PlatformConnection).filter(
            PlatformConnection.platform == platform
        )

    content = query.order_by(Content.published_at.desc()).offset(skip).limit(limit).all()
    return content


# ============================================================================
# INCOME ROUTES
# ============================================================================

@income_router.post("/", response_model=IncomeResponse)
async def create_income(
    creator_id: int,
    income: IncomeCreate,
    db: Session = Depends(get_db)
):
    """Create a new income record."""
    db_income = Income(
        creator_id=creator_id,
        **income.model_dump()
    )
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income


@income_router.get("/{income_id}", response_model=IncomeResponse)
async def get_income(income_id: int, db: Session = Depends(get_db)):
    """Get income record by ID."""
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    return income


@income_router.get("/creator/{creator_id}", response_model=List[IncomeResponse])
async def list_creator_income(
    creator_id: int,
    platform: Optional[PlatformEnum] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List income for a creator."""
    query = db.query(Income).filter(Income.creator_id == creator_id)

    if platform:
        query = query.filter(Income.platform == platform)
    if date_from:
        query = query.filter(Income.income_date >= date_from)
    if date_to:
        query = query.filter(Income.income_date <= date_to)

    income = query.order_by(Income.income_date.desc()).offset(skip).limit(limit).all()
    return income


@income_router.get("/creator/{creator_id}/stats", response_model=IncomeStats)
async def get_income_stats(
    creator_id: int,
    date_from: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get income statistics for a creator."""
    from sqlalchemy import func

    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=365)

    query = db.query(Income).filter(
        Income.creator_id == creator_id,
        Income.income_date >= date_from
    )

    # Total income
    total_income = query.with_entities(func.sum(Income.amount)).scalar() or 0

    # Income by platform
    income_by_platform = {}
    for platform in PlatformEnum:
        platform_income = query.filter(Income.platform == platform).with_entities(
            func.sum(Income.amount)
        ).scalar() or 0
        income_by_platform[platform.value] = platform_income

    # Income by type
    from app.db.models import IncomeTypeEnum
    income_by_type = {}
    for income_type in IncomeTypeEnum:
        type_income = query.filter(Income.income_type == income_type).with_entities(
            func.sum(Income.amount)
        ).scalar() or 0
        income_by_type[income_type.value] = type_income

    # Calculate growth rate (simple month-over-month)
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

    current_month_income = db.query(Income).filter(
        Income.creator_id == creator_id,
        Income.income_date >= current_month_start
    ).with_entities(func.sum(Income.amount)).scalar() or 0

    previous_month_income = db.query(Income).filter(
        Income.creator_id == creator_id,
        Income.income_date >= previous_month_start,
        Income.income_date < current_month_start
    ).with_entities(func.sum(Income.amount)).scalar() or 1  # Avoid division by zero

    growth_rate = ((current_month_income - previous_month_income) / previous_month_income) * 100

    # Average monthly income
    months_count = (datetime.utcnow() - date_from).days / 30
    average_monthly_income = total_income / max(months_count, 1)

    return IncomeStats(
        total_income=total_income,
        income_by_platform=income_by_platform,
        income_by_type=income_by_type,
        average_monthly_income=average_monthly_income,
        growth_rate=growth_rate
    )


# ============================================================================
# ATTRIBUTION ROUTES
# ============================================================================

@attribution_router.post("/run/{creator_id}")
async def run_attribution(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """Run attribution analysis for a creator."""
    attribution_service = AttributionService(db)
    results = await attribution_service.run_attribution(creator_id)

    return {
        "creator_id": creator_id,
        "attributions_created": len(results),
        "message": "Attribution analysis completed"
    }


@attribution_router.get("/creator/{creator_id}", response_model=List[AttributionResponse])
async def get_creator_attributions(
    creator_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get attributions for a creator."""
    attributions = db.query(Attribution).filter(
        Attribution.creator_id == creator_id
    ).order_by(Attribution.created_at.desc()).offset(skip).limit(limit).all()

    return attributions


# ============================================================================
# FORECAST ROUTES
# ============================================================================

@forecast_router.post("/creator/{creator_id}", response_model=ForecastResponse)
async def generate_forecast(
    creator_id: int,
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    """Generate income forecast for a creator."""
    forecast_service = ForecastService(db)
    forecast = await forecast_service.generate_forecast(
        creator_id=creator_id,
        horizon_days=request.horizon_days,
        platform=request.platform,
        income_type=request.income_type
    )

    return forecast


@forecast_router.get("/creator/{creator_id}", response_model=ForecastResponse)
async def get_latest_forecast(
    creator_id: int,
    platform: Optional[PlatformEnum] = None,
    db: Session = Depends(get_db)
):
    """Get the latest forecast for a creator."""
    query = db.query(ForecastData).filter(
        ForecastData.creator_id == creator_id
    )

    if platform:
        query = query.filter(ForecastData.platform == platform)

    forecast_data = query.order_by(ForecastData.generated_at.desc()).limit(90).all()

    if not forecast_data:
        raise HTTPException(status_code=404, detail="No forecast data found")

    from app.api.schemas import ForecastDataPoint
    return ForecastResponse(
        creator_id=creator_id,
        forecast_data=[
            ForecastDataPoint(
                date=f.forecast_date,
                predicted_income=f.predicted_income,
                confidence_lower=f.confidence_lower,
                confidence_upper=f.confidence_upper
            )
            for f in forecast_data
        ],
        total_predicted_income=sum(f.predicted_income for f in forecast_data),
        model_version=forecast_data[0].model_version,
        generated_at=forecast_data[0].generated_at
    )


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@dashboard_router.get("/creator/{creator_id}", response_model=DashboardOverview)
async def get_dashboard(creator_id: int, db: Session = Depends(get_db)):
    """Get complete dashboard overview for a creator."""
    # Get creator
    creator = db.query(Creator).filter(Creator.id == creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    # This would be implemented with proper aggregations
    # Simplified for now
    return DashboardOverview(
        creator=CreatorResponse.model_validate(creator),
        total_income_30d=0.0,
        total_income_90d=0.0,
        income_forecast_30d=0.0,
        content_metrics=ContentMetrics(
            total_views=0,
            total_likes=0,
            total_comments=0,
            average_engagement_rate=0.0,
            top_performing_content=[]
        ),
        income_stats=IncomeStats(
            total_income=0.0,
            income_by_platform={},
            income_by_type={},
            average_monthly_income=0.0,
            growth_rate=0.0
        ),
        recent_attributions=[],
        top_earning_content=[]
    )


# ============================================================================
# SYNC ROUTES
# ============================================================================

@sync_router.post("/creator/{creator_id}", response_model=SyncStatus)
async def sync_creator_data(
    creator_id: int,
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """Trigger data sync from a platform."""
    # This would trigger a Celery task
    task = sync_platform_data.delay(
        creator_id=creator_id,
        platform=request.platform.value,
        sync_content=request.sync_content,
        sync_income=request.sync_income
    )

    return SyncStatus(
        platform=request.platform,
        status="pending",
        content_synced=0,
        income_synced=0,
        started_at=datetime.utcnow()
    )


@sync_router.get("/status/{task_id}")
async def get_sync_status(task_id: str):
    """Get status of a sync task."""
    from app.celery_app import celery_app

    task = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
