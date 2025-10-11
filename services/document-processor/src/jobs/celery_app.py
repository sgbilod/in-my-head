"""
Celery application configuration for background job processing.

This module configures Celery with Redis as both broker and result backend.
"""

import os
from celery import Celery
from kombu import Exchange, Queue

# Redis connection URL
REDIS_URL = os.getenv(
    "REDIS_URL", "redis://localhost:6379/0"
)

# Create Celery application
celery_app = Celery(
    "in_my_head_jobs",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "jobs.tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_backend=REDIS_URL,
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,

    # Task routing
    task_routes={
        "jobs.tasks.process_document_task": {"queue": "document_processing"},
        "jobs.tasks.parse_document_task": {"queue": "parsing"},
        "jobs.tasks.preprocess_text_task": {"queue": "preprocessing"},
        "jobs.tasks.generate_embeddings_task": {"queue": "embeddings"},
        "jobs.tasks.extract_metadata_task": {"queue": "metadata"},
        "jobs.tasks.store_in_vector_db_task": {"queue": "storage"},
    },

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit

    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    task_retry_backoff=True,
    task_retry_backoff_max=600,
    task_retry_jitter=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_track_started=True,

    # Queue configuration
    task_queues=(
        Queue(
            "document_processing",
            Exchange("document_processing"),
            routing_key="document_processing",
            queue_arguments={"x-max-priority": 10},
        ),
        Queue(
            "parsing",
            Exchange("parsing"),
            routing_key="parsing",
            queue_arguments={"x-max-priority": 8},
        ),
        Queue(
            "preprocessing",
            Exchange("preprocessing"),
            routing_key="preprocessing",
            queue_arguments={"x-max-priority": 7},
        ),
        Queue(
            "embeddings",
            Exchange("embeddings"),
            routing_key="embeddings",
            queue_arguments={"x-max-priority": 6},
        ),
        Queue(
            "metadata",
            Exchange("metadata"),
            routing_key="metadata",
            queue_arguments={"x-max-priority": 6},
        ),
        Queue(
            "storage",
            Exchange("storage"),
            routing_key="storage",
            queue_arguments={"x-max-priority": 5},
        ),
    ),

    # Default queue
    task_default_queue="document_processing",
    task_default_exchange="document_processing",
    task_default_routing_key="document_processing",
)

# Beat schedule for periodic tasks (if needed)
celery_app.conf.beat_schedule = {
    "cleanup-expired-jobs": {
        "task": "jobs.tasks.cleanup_expired_jobs",
        "schedule": 3600.0,  # Run every hour
    },
}

if __name__ == "__main__":
    celery_app.start()
