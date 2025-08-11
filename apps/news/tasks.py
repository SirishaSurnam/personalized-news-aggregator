from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from django.db.models import Q
# from apps.news.models import Article, Category  # Keep only one import
from apps.ai_services import CachedSummarizer, BiasDetector
from apps.ai_services.news_fetcher import NewsFetcher
import psutil  # Add this import
import time
# from django.db import models
from .models import Article
# from apps.ai_services.gemini_client import GeminiService

logger = logging.getLogger(__name__)


@shared_task(bind=True, priority='medium', max_retries=3)
def fetch_latest_news(self):
    """Fetch latest news articles from various sources."""
    try:
        fetcher = NewsFetcher()
        sources = ['newsapi', 'guardian', 'rss']
        total_articles = 0
        for source in sources:
            try:
                count = fetcher.fetch_from_source(source)
                total_articles += count
                logger.info(f"Fetched {count} articles from {source}")
            except Exception as e:
                logger.error(f"Error fetching from {source}: {str(e)}")
        logger.info(f"Total articles fetched: {total_articles}")
        return f"Successfully fetched {total_articles} articles"
    except Exception as e:
        logger.error(f"Error in fetch_latest_news: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(bind=True, priority='high', max_retries=3)
def process_article_ai(self, article_id):
    """Process article AI (summary and bias detection)"""
    start_time = time.time()
    process = psutil.Process()
    logger.info(f"Starting AI processing for article {article_id}")
    logger.info(
        f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f}MB")
    try:
        article = Article.objects.get(id=article_id)
        content = article.content or article.description or ""
        logger.info(f"[📝] Processing article {article.id} titled '{article.title}' — content length: {len(content)}")
        if not content:
            logger.warning(f"[⚠️] Empty content for article {article_id}")
            return
        summarizer = CachedSummarizer()
        summary = summarizer.summarize(content)
        detector = BiasDetector()
        bias_score = detector.detect_bias(content)
        article.summary = summary
        article.bias_score = bias_score
        article.save()
        duration = time.time() - start_time
        logger.info(
            f"[✔] Saved summary for article {article.id} in {duration:.2f}s")
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        self.retry(countdown=60, max_retries=3)
    except Exception as e:
        logger.error(f"[✘] Error processing article {article_id}: {e}")
        self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, priority='low', max_retries=3)
def cleanup_old_articles(self):
    """Remove articles older than 30 days."""
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        old_articles = Article.objects.filter(published_date__lt=cutoff_date)
        count = old_articles.count()
        old_articles.delete()
        logger.info(f"Cleaned up {count} old articles")
        return f"Cleaned up {count} old articles"
    except Exception as e:
        logger.error(f"Error in cleanup_old_articles: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(bind=True, priority='medium', max_retries=3)
def process_pending_articles(self, article_id):
    """Process articles that haven't been analyzed by AI yet"""
    try:
        pending_articles = Article.objects.filter(
            Q(summary='') | Q(bias_score='UNKNOWN')
        )[:10]  # Limit to 10 at a time
        for article in pending_articles:
            process_article_ai.delay(article.id)
        count = pending_articles.count()
        logger.info(f"Queued {count} articles for AI processing")
        return f"Queued {count} articles for processing"
    except Exception as e:
        logger.error(f"Error in process_pending_articles: {str(e)}")
        self.retry(countdown=60, max_retries=3)
