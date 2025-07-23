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
# config/celery.py (add these tasks)

'''
@app.task
def process_article_ai(article_id):
    from apps.news.models import Article
    from config.ai_services import AdvancedSummarizer, BiasDetector

    article = Article.objects.get(id=article_id)
    summarizer = AdvancedSummarizer()
    bias_detector = BiasDetector()

    try:
        # Generate summary
        summary = summarizer.summarize(article.content)
        article.summary = summary

        # Detect bias
        bias_result = bias_detector.detect_bias(article.content)
        article.bias_score = bias_result['bias_type']
        article.bias_confidence = bias_result['confidence']

        article.save()
    except Exception as e:
        print(f"Error processing article {article_id}: {e}")


@app.task
def update_user_preferences(user_id):
    from apps.news.models import User, UserActivity, UserPreference

    user = User.objects.get(id=user_id)
    activities = UserActivity.objects.filter(user=user)

    # Update preferences based on activity
    preference, created = UserPreference.objects.get_or_create(user=user)

    # Analyze categories
    categories = activities.values_list('article__categories__name', flat=True)
    preference.preferred_categories = list(set(categories))

    # Analyze sources
    sources = activities.values_list('article__source', flat=True)
    preference.preferred_sources = list(set(sources))

    preference.save()

# config/celery.py (Add these optimized tasks)


# config/celery.py
# config/celery.py
@app.task(bind=True, max_retries=3)
def process_article_ai(self, article_id):
    from apps.news.models import Article
    from apps.ai_services import OptimizedSummarizer, BiasDetector

    try:
        article = Article.objects.get(id=article_id)

        # Generate summary
        summarizer = OptimizedSummarizer()
        summary = summarizer.summarize(article.content)
        article.summary = summary

        # Detect bias
        bias_detector = BiasDetector()
        bias_result = bias_detector.detect_bias(article.content)
        article.bias_score = bias_result

        article.save()

    except Exception as e:
        print(f"Error processing article {article_id}: {e}")
        raise self.retry(exc=e, countdown=60 ** self.request.retries)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
'''
