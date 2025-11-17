"""
Celery tasks for analytics and ML operations.
"""
from celery import Task
from typing import Optional
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.base import SessionLocal
from app.db.models import Creator
from app.services.attribution_service import AttributionService
from app.services.forecast_service import ForecastService


class DatabaseTask(Task):
    """Base task that provides database session."""

    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def run_attribution_for_creator(self, creator_id: int):
    """
    Run attribution analysis for a specific creator.

    Args:
        creator_id: Creator ID
    """
    db = self.db
    attribution_service = AttributionService(db)

    try:
        attributions = await attribution_service.run_attribution(creator_id)

        return {
            "creator_id": creator_id,
            "attributions_created": len(attributions),
            "status": "success"
        }
    except Exception as e:
        return {
            "creator_id": creator_id,
            "status": "error",
            "error": str(e)
        }


@celery_app.task(base=DatabaseTask, bind=True)
def run_attribution_all_creators(self):
    """
    Run attribution for all active creators.
    Periodic task.
    """
    db = self.db

    creators = db.query(Creator).filter(Creator.is_active == True).all()

    results = []
    for creator in creators:
        result = run_attribution_for_creator.delay(creator.id)
        results.append({
            "creator_id": creator.id,
            "task_id": result.id
        })

    return {
        "total_creators": len(results),
        "tasks": results
    }


@celery_app.task(base=DatabaseTask, bind=True)
def generate_forecast_for_creator(self, creator_id: int, horizon_days: int = 90):
    """
    Generate income forecast for a creator.

    Args:
        creator_id: Creator ID
        horizon_days: Number of days to forecast
    """
    db = self.db
    forecast_service = ForecastService(db)

    try:
        forecast = await forecast_service.generate_forecast(
            creator_id=creator_id,
            horizon_days=horizon_days
        )

        return {
            "creator_id": creator_id,
            "forecast_days": horizon_days,
            "total_predicted_income": forecast.total_predicted_income,
            "status": "success"
        }
    except Exception as e:
        return {
            "creator_id": creator_id,
            "status": "error",
            "error": str(e)
        }


@celery_app.task(base=DatabaseTask, bind=True)
def generate_forecasts_all_creators(self):
    """
    Generate forecasts for all active creators.
    Periodic task.
    """
    db = self.db

    creators = db.query(Creator).filter(Creator.is_active == True).all()

    results = []
    for creator in creators:
        result = generate_forecast_for_creator.delay(creator.id)
        results.append({
            "creator_id": creator.id,
            "task_id": result.id
        })

    return {
        "total_creators": len(results),
        "tasks": results
    }


@celery_app.task(base=DatabaseTask, bind=True)
def train_attribution_model(self, creator_id: Optional[int] = None):
    """
    Train or retrain the attribution model.

    Args:
        creator_id: Optional creator ID for creator-specific model
    """
    db = self.db
    attribution_service = AttributionService(db)

    try:
        attribution_service.train_model(creator_id)

        return {
            "status": "success",
            "creator_id": creator_id,
            "message": "Model training completed"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
