from celery import Celery
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "reviveiq_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Standard configurations
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="app.core.celery_app.run_background_pipeline_task")
def run_background_pipeline_task(customer_id: int):
    """Background task executing multi-agent pipeline for a single account."""
    from app.core.database import SessionLocal
    from app.services.agents.orchestrator import orchestrator
    
    print(f"Celery: Executing background risk pipeline for customer {customer_id}...")
    db = SessionLocal()
    try:
        orchestrator.run_customer_pipeline(db, customer_id)
    finally:
        db.close()
    print("Celery: Background execution completed.")
