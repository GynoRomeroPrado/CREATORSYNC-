"""
Celery application configuration.
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "creatorsync",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.sync_tasks", "app.tasks.analytics_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "sync-all-platforms-daily": {
        "task": "app.tasks.sync_tasks.sync_all_creators",
        "schedule": 86400.0,  # Every 24 hours
    },
    "run-attribution-hourly": {
        "task": "app.tasks.analytics_tasks.run_attribution_all_creators",
        "schedule": 3600.0,  # Every hour
    },
    "generate-forecasts-daily": {
        "task": "app.tasks.analytics_tasks.generate_forecasts_all_creators",
        "schedule": 86400.0,  # Every 24 hours
    },
}
