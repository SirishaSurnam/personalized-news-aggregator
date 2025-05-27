from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from django.db import models
from .models import Article, Category

from apps.ai_services.gemini_client import GeminiService
from apps.ai_services.news_fetcher import NewsFetcher

logger = logging.getLogger(__name__)

@shared_task
def fetch_latest_news():
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

@shared_task
def process_article_ai(article_id):
    """Process article with AI for summary and bias detection."""
    try:
        article = Article.objects.get(id=article_id)
        gemini = GeminiService()

        # Generate summary if not exists
        if not article.summary:
            summary = gemini.summarize_article(article.content or article.description)
            article.summary = summary

        # Detect bias if unknown
        if article.bias_score == 'UNKNOWN':
            bias = gemini.detect_bias(article.content or article.description)
            article.bias_score = bias

        article.save()
        logger.info(f"Processed article {article_id} with AI")
        return f"Processed article: {article.title[:50]}"

    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        return f"Article {article_id} not found"
    except Exception as e:
        logger.error(f"Error processing article {article_id}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def cleanup_old_articles():
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

@shared_task
def process_pending_articles():
    """Process articles that haven't been analyzed by AI yet."""
    try:
        pending_articles = Article.objects.filter(
            models.Q(summary='') | models.Q(bias_score='UNKNOWN')
        )[:10]  # Limit processing to 10 at a time

        for article in pending_articles:
            process_article_ai.delay(article.id)

        count = pending_articles.count()
        logger.info(f"Queued {count} articles for AI processing")
        return f"Queued {count} articles for processing"

    except Exception as e:
        logger.error(f"Error in process_pending_articles: {str(e)}")
        return f"Error: {str(e)}"
