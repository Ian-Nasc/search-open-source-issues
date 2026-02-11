from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "ossearch",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_scheduler="celery.beat:Scheduler",
    beat_schedule={
        "scrape-all-companies": {
            "task": "app.tasks.scraping.scrape_all_companies",
            "schedule": crontab(hour=f"*/{settings.SCRAPE_INTERVAL_HOURS}"),
        },
        "generate-missing-embeddings": {
            "task": "app.tasks.embeddings.generate_missing_embeddings",
            "schedule": crontab(
                hour=f"*/{settings.SCRAPE_INTERVAL_HOURS}", minute=30
            ),
        },
    },
)

celery.autodiscover_tasks(["app.tasks"])
