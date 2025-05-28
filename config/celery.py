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

# Auto-discover tasks in all registered Django app configs (e.g., apps/news/tasks.py).
app.autodiscover_tasks()

# Optional: A simple debug task
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

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