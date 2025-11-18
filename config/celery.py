import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create a Celery app instance

app = Celery('news_aggregator')

# Load task configuration from Django settings.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix in settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')


# Add these optimizations
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_track_started=True,
    worker_max_memory_per_child=500 * 1024 * 1024,  # 500MB
)

app.conf.task_routes = {
    'apps.news.tasks.process_article_ai': {'queue': 'high'},
    'apps.news.tasks.fetch_latest_news': {'queue': 'medium'},
    'apps.news.tasks.cleanup_old_articles': {'queue': 'low'},
    'apps.news.tasks.process_pending_articles': {'queue': 'medium'},
}


# Auto-discover tasks in all registered Django app configs.
# For example, tasks can be placed in apps/news/tasks.py.
app.autodiscover_tasks()

# Optional: A simple debug task

app.conf.beat_schedule = {
    'process-articles-every-hour': {
        'task': 'apps.news.tasks.process_pending_articles',
        'schedule': crontab(minute=0, hour='*/1'),  # every 60 minutes
    },
}


# Define periodic tasks for Celery Beat
app.conf.beat_schedule = {
    'fetch-news-every-hour': {
        'task': 'apps.news.tasks.fetch_latest_news',
        'schedule': crontab(minute=0),  # Run at the beginning of every hour
        'args': (),
    },
    'process-pending-articles-every-30-minutes': {
        'task': 'apps.news.tasks.process_pending_articles',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
        'args': (),
    },
    'cleanup-old-articles-daily': {
        'task': 'apps.news.tasks.cleanup_old_articles',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM UTC
        'args': (),
    },
}


