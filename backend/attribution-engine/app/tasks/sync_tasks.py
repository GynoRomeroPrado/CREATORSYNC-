"""
Celery tasks for syncing data from platforms.
"""
from celery import Task
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.base import SessionLocal
from app.db.models import Creator, PlatformConnection, Content, Income, PlatformEnum
from app.integrations.youtube import YouTubeIntegration
from app.integrations.tiktok import TikTokIntegration


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
def sync_platform_data(
    self,
    creator_id: int,
    platform: str,
    sync_content: bool = True,
    sync_income: bool = True,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    Sync data from a platform for a creator.

    Args:
        creator_id: Creator ID
        platform: Platform name (youtube, tiktok, etc.)
        sync_content: Whether to sync content
        sync_income: Whether to sync income
        date_from: Optional start date (ISO format)
        date_to: Optional end date (ISO format)
    """
    db = self.db

    # Get platform connection
    connection = db.query(PlatformConnection).filter(
        PlatformConnection.creator_id == creator_id,
        PlatformConnection.platform == platform,
        PlatformConnection.is_active == True
    ).first()

    if not connection:
        return {"error": f"No active {platform} connection found"}

    # Parse dates
    date_from_dt = datetime.fromisoformat(date_from) if date_from else None
    date_to_dt = datetime.fromisoformat(date_to) if date_to else None

    # Get appropriate integration
    integration = _get_integration(platform, connection.access_token)

    stats = {
        "platform": platform,
        "content_synced": 0,
        "income_synced": 0,
        "errors": []
    }

    try:
        # Sync content
        if sync_content:
            content_data = await integration.get_content(
                user_id=connection.platform_user_id,
                date_from=date_from_dt,
                date_to=date_to_dt
            )

            for content_item in content_data:
                # Check if content already exists
                existing = db.query(Content).filter(
                    Content.platform_connection_id == connection.id,
                    Content.platform_content_id == content_item["platform_content_id"]
                ).first()

                if existing:
                    # Update existing
                    for key, value in content_item.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.last_metrics_update = datetime.utcnow()
                else:
                    # Create new
                    new_content = Content(
                        creator_id=creator_id,
                        platform_connection_id=connection.id,
                        **content_item
                    )
                    db.add(new_content)

                stats["content_synced"] += 1

        # Sync income
        if sync_income:
            income_data = await integration.get_income(
                user_id=connection.platform_user_id,
                date_from=date_from_dt,
                date_to=date_to_dt
            )

            for income_item in income_data:
                # Check if income already exists
                existing = db.query(Income).filter(
                    Income.creator_id == creator_id,
                    Income.source_id == income_item.get("source_id")
                ).first()

                if not existing and income_item.get("source_id"):
                    new_income = Income(
                        creator_id=creator_id,
                        platform=PlatformEnum(platform),
                        **income_item
                    )
                    db.add(new_income)
                    stats["income_synced"] += 1

        # Update last sync time
        connection.last_synced_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        stats["errors"].append(str(e))
        raise

    finally:
        await integration.close()

    return stats


@celery_app.task(base=DatabaseTask, bind=True)
def sync_all_creators(self):
    """
    Sync data for all active creators.
    Run as periodic task.
    """
    db = self.db

    # Get all active platform connections
    connections = db.query(PlatformConnection).filter(
        PlatformConnection.is_active == True
    ).all()

    results = []

    for connection in connections:
        # Skip if synced recently (within last 6 hours)
        if connection.last_synced_at:
            hours_since_sync = (datetime.utcnow() - connection.last_synced_at).total_seconds() / 3600
            if hours_since_sync < 6:
                continue

        # Trigger sync task
        result = sync_platform_data.delay(
            creator_id=connection.creator_id,
            platform=connection.platform.value,
            sync_content=True,
            sync_income=True
        )

        results.append({
            "creator_id": connection.creator_id,
            "platform": connection.platform.value,
            "task_id": result.id
        })

    return {
        "synced_connections": len(results),
        "tasks": results
    }


def _get_integration(platform: str, access_token: Optional[str]):
    """Get the appropriate platform integration."""
    if platform == "youtube":
        return YouTubeIntegration(access_token)
    elif platform == "tiktok":
        return TikTokIntegration(access_token)
    # Add more platforms as needed
    else:
        raise ValueError(f"Unsupported platform: {platform}")
