import requests
import feedparser
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from apps.news.models import Article, Category  # Import your models

logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self):
        # Initialize API keys from Django settings
        # Ensure NEWSAPI_KEY and GUARDIAN_API_KEY are defined in your settings.py
        self.newsapi_key = getattr(settings, 'NEWSAPI_KEY', None)
        self.guardian_key = getattr(settings, 'GUARDIAN_API_KEY', None)

    def fetch_from_source(self, source):
        """Fetch articles from specified source"""
        if source == 'newsapi':
            return self.fetch_from_newsapi()
        elif source == 'guardian':
            return self.fetch_from_guardian()
        elif source == 'rss':
            return self.fetch_from_rss()
        else:
            logger.error(f"Unknown source: {source}")
            return 0

    def fetch_from_newsapi(self):
        """Fetch articles from NewsAPI"""
        if not self.newsapi_key:
            logger.warning(
                "NewsAPI key not configured. Please set NEWSAPI_KEY in your Django settings.")
            return 0

        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': self.newsapi_key,
                'country': 'us',  # Consider making this configurable
                # Number of results to return per request (max 100 for developer, 20 for free)
                'pageSize': 20,
                'sortBy': 'publishedAt'
            }

            # Make the GET request to NewsAPI
            response = requests.get(
                url, params=params, timeout=30)  # 30 seconds timeout
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            articles_created = 0
            for item in data.get('articles', []):
                if self.create_article_from_newsapi(item):
                    articles_created += 1

            logger.info(f"Created {articles_created} articles from NewsAPI")
            return articles_created

        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"HTTP error occurred while fetching from NewsAPI: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Error during request to NewsAPI: {req_err}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred fetching from NewsAPI: {str(e)}")
        return 0

    def fetch_from_guardian(self):
        """Fetch articles from Guardian API"""
        if not self.guardian_key:
            logger.warning(
                "Guardian API key not configured. Please set GUARDIAN_API_KEY in your Django settings.")
            return 0

        try:
            url = "https://content.guardianapis.com/search"
            params = {
                'api-key': self.guardian_key,
                # headline,standfirst,body,byline,thumbnail,publication
                'show-fields': 'trailText,body,byline',
                'page-size': 20,  # Max 50 per page
                'order-by': 'newest'
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            articles_created = 0
            for item in data.get('response', {}).get('results', []):
                if self.create_article_from_guardian(item):
                    articles_created += 1

            logger.info(f"Created {articles_created} articles from Guardian")
            return articles_created

        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"HTTP error occurred while fetching from Guardian: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Error during request to Guardian API: {req_err}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred fetching from Guardian: {str(e)}")
        return 0

    def fetch_from_rss(self):
        """Fetch articles from RSS feeds"""
        # Consider moving this list to Django settings or a database model for easier management
        rss_feeds = [
            'http://feeds.bbci.co.uk/news/rss.xml',
            'http://rss.cnn.com/rss/edition.rss',
            'https://feeds.reuters.com/reuters/topNews',
            'https://techcrunch.com/feed/',
            'https://feeds.arstechnica.com/arstechnica/index'
        ]

        articles_created = 0
        for feed_url in rss_feeds:
            try:
                logger.info(f"Fetching RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                # Limit to a certain number of entries per feed to avoid overwhelming the system
                # Process up to 5 newest entries
                for entry in feed.entries[:5]:
                    if self.create_article_from_rss(entry, feed_url):
                        articles_created += 1
            except Exception as e:
                logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")

        logger.info(f"Created {articles_created} articles from RSS feeds")
        return articles_created

    def create_article_from_newsapi(self, item):
        """Create article from NewsAPI data, ensuring not to create duplicates."""
        try:
            article_url = item.get('url')
            article_title = item.get('title')

            # Skip articles without URL or title, as they are essential
            if not article_url or not article_title:
                logger.warning(
                    f"Skipping NewsAPI item due to missing URL or title: {item}")
                return False

            # Check if article already exists to prevent duplicates
            if Article.objects.filter(url=article_url).exists():
                logger.info(f"Article already exists (NewsAPI): {article_url}")
                return False

            published_date_str = item.get('publishedAt')
            published_date = timezone.now()  # Default to now if parsing fails
            if published_date_str:
                try:
                    # NewsAPI uses ISO 8601 format
                    published_date = datetime.fromisoformat(
                        published_date_str.replace('Z', '+00:00'))
                    # Ensure it's timezone-aware (Django expects this)
                    if timezone.is_naive(published_date):
                        published_date = timezone.make_aware(
                            published_date, timezone.utc)
                except ValueError:
                    logger.warning(
                        f"Invalid date format for NewsAPI article: '{published_date_str}'. Using current time."
                    )

            # Create article instance
            article = Article.objects.create(
                # Ensure title fits model constraints
                title=article_title[:500],
                url=article_url,
                description=item.get('description', '')[
                    :1000],  # Limit description length
                content=item.get('content', '')[:5000],  # Limit content length
                author=item.get('author', '')[:200],  # Limit author length
                source=item.get('source', {}).get('name', 'NewsAPI')[
                    :200],  # Limit source name length
                published_date=published_date
            )
            logger.info(f"Created article (NewsAPI): {article.title}")
            self.auto_categorize_article(article)
            return True

        except Exception as e:
            logger.error(
                f"Error creating article from NewsAPI item '{item.get('title')}': {str(e)}")
            return False

    def create_article_from_guardian(self, item):
        """Create article from Guardian API data, ensuring not to create duplicates."""
        try:
            article_url = item.get('webUrl')
            article_title = item.get('webTitle')

            if not article_url or not article_title:
                logger.warning(
                    f"Skipping Guardian item due to missing URL or title: {item}")
                return False

            if Article.objects.filter(url=article_url).exists():
                logger.info(
                    f"Article already exists (Guardian): {article_url}")
                return False

            published_date_str = item.get('webPublicationDate')
            published_date = timezone.now()
            if published_date_str:
                try:
                    published_date = datetime.fromisoformat(
                        published_date_str.replace('Z', '+00:00'))
                    if timezone.is_naive(published_date):
                        published_date = timezone.make_aware(
                            published_date, timezone.utc)
                except ValueError:
                    logger.warning(
                        f"Invalid date format for Guardian article: '{published_date_str}'. Using current time."
                    )

            fields = item.get('fields', {})
            description = fields.get('trailText', '')
            # Guardian content can be HTML
            content_html = fields.get('body', '')
            author = fields.get('byline', '')

            # Clean HTML from content using BeautifulSoup
            content_text = ''
            if content_html:
                soup = BeautifulSoup(content_html, 'html.parser')
                content_text = soup.get_text(
                    separator='\n\n', strip=True)  # Get clean text

            article = Article.objects.create(
                title=article_title[:500],
                url=article_url,
                description=description[:1000],
                content=content_text[:5000],
                author=author[:200],
                source='The Guardian',  # Static source for Guardian API
                published_date=published_date
            )
            logger.info(f"Created article (Guardian): {article.title}")
            # Pass sectionName for better categorization if available
            self.auto_categorize_article(article, item.get('sectionName', ''))
            return True

        except Exception as e:
            logger.error(
                f"Error creating article from Guardian item '{item.get('webTitle')}': {str(e)}")
            return False

    def create_article_from_rss(self, entry, feed_url):
        """Create article from RSS entry, ensuring not to create duplicates."""
        try:
            article_url = entry.get('link')
            article_title = entry.get('title')

            if not article_url or not article_title:
                logger.warning(
                    f"Skipping RSS entry from {feed_url} due to missing link or title: {entry}")
                return False

            if Article.objects.filter(url=article_url).exists():
                logger.info(
                    f"Article already exists (RSS: {feed_url}): {article_url}")
                return False

            published_date = timezone.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    # feedparser provides a time.struct_time object
                    dt_naive = datetime(*entry.published_parsed[:6])
                    published_date = timezone.make_aware(
                        dt_naive, timezone.utc)  # Assume UTC if not specified
                except Exception as e:
                    logger.warning(
                        f"Invalid date format for RSS article ({feed_url}): {entry.get('published_parsed')} - {e}. Using current time."
                    )
            # Fallback to updated_parsed
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    dt_naive = datetime(*entry.updated_parsed[:6])
                    published_date = timezone.make_aware(
                        dt_naive, timezone.utc)
                except Exception as e:
                    logger.warning(
                        f"Invalid updated_date format for RSS article ({feed_url}): {entry.get('updated_parsed')} - {e}. Using current time."
                    )

            source_name = self.get_source_from_url(feed_url)

            # RSS summary can be HTML
            description_html = getattr(entry, 'summary', '')
            description_text = ''
            if description_html:
                soup = BeautifulSoup(description_html, 'html.parser')
                description_text = soup.get_text(separator='\n', strip=True)

            # RSS feeds usually provide summaries, not full content.
            # Full content might require scraping the article URL, which is a more complex task.
            content = ''  # Placeholder for full content if you decide to scrape later
            if hasattr(entry, 'content'):  # Some feeds might have a 'content' field
                # entry.content is often a list of content objects
                if isinstance(entry.content, list) and entry.content:
                    content_html_full = entry.content[0].get('value', '')
                    if content_html_full:
                        soup_full = BeautifulSoup(
                            content_html_full, 'html.parser')
                        content = soup_full.get_text(
                            separator='\n\n', strip=True)

            article = Article.objects.create(
                title=article_title[:500],
                url=article_url,
                description=description_text[:1000],
                # Use parsed content if available
                content=content[:5000] if content else '',
                author=getattr(entry, 'author', '')[:200],
                source=source_name[:200],
                published_date=published_date
            )
            logger.info(
                f"Created article (RSS: {source_name}): {article.title}")
            self.auto_categorize_article(article)
            return True

        except Exception as e:
            logger.error(
                f"Error creating article from RSS entry '{entry.get('title')}' from {feed_url}: {str(e)}")
            return False

    def get_source_from_url(self, url):
        """Extract a more human-readable source name from feed URL."""
        # This can be expanded with more sophisticated domain parsing if needed
        if 'bbc.co.uk' in url or 'bbc.com' in url:
            return 'BBC News'
        elif 'cnn.com' in url:
            return 'CNN'
        elif 'reuters.com' in url:
            return 'Reuters'
        elif 'techcrunch.com' in url:
            return 'TechCrunch'
        elif 'arstechnica.com' in url:
            return 'Ars Technica'
        # Fallback to a generic name or try to parse domain
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            if domain:
                # e.g. 'Google' from 'news.google.com'
                return domain.split('.')[0].capitalize()
        except ImportError:  # Should not happen in modern Python
            pass
        return 'RSS Feed'

    def auto_categorize_article(self, article, section=None):
        """
        Automatically categorize article based on section (if provided),
        then title and description keywords.
        """
        try:
            categories_to_add_names = set()  # Use a set to avoid duplicate category names

            # Category mapping (keywords are case-insensitive)
            # Consider moving this to a more configurable location (e.g., JSON file, database)
            category_keywords = {
                'Technology': ['tech', 'software', 'computer', 'internet', 'digital', 'ai', 'artificial intelligence', 'gadget', 'startup', 'cybersecurity', 'innovation', 'platform', 'app', 'device', 'data', 'cloud'],
                'Politics': ['election', 'government', 'congress', 'senate', 'political', 'policy', 'president', 'vote', 'parliament', 'legislation', 'diplomacy', 'white house', 'candidate'],
                'Business': ['business', 'economy', 'market', 'finance', 'stock', 'company', 'invest', 'trade', 'economic', 'corporate', 'industry', 'merger', 'acquisition', 'earnings', 'inflation', 'gdp'],
                'Sports': ['sport', 'football', 'basketball', 'soccer', 'game', 'player', 'team', 'match', 'olympics', 'league', 'championship', 'nfl', 'nba', 'mlb', 'tournament'],
                'Health': ['health', 'medical', 'hospital', 'doctor', 'medicine', 'disease', 'wellness', 'covid', 'pandemic', 'virus', 'vaccine', 'healthcare', 'mental health', 'nutrition'],
                'Science': ['science', 'research', 'study', 'discovery', 'scientist', 'space', 'biology', 'physics', 'chemistry', 'astronomy', 'environment', 'climate', 'nasa'],
                'Entertainment': ['entertainment', 'movie', 'film', 'celebrity', 'music', 'tv', 'hollywood', 'art', 'culture', 'theatre', 'award', 'series', 'actor', 'actress', 'album'],
                'World News': ['world', 'international', 'global', 'country', 'geopolitics', 'conflict', 'diplomacy', 'united nations', 'foreign affairs', 'war', 'peace'],
                'Local News': ['local', 'city', 'community', 'town', 'neighborhood', 'regional', 'state'],
                'Opinion': ['opinion', 'editorial', 'commentary', 'viewpoint'],
                'Lifestyle': ['lifestyle', 'travel', 'food', 'fashion', 'home', 'garden', 'well-being'],
                'Education': ['education', 'school', 'university', 'college', 'student', 'teacher', 'learning'],
            }

            # 1. Check section first (often more reliable if available, e.g., from Guardian)
            if section:
                section_lower = section.lower()
                for cat_name, keywords in category_keywords.items():
                    # Check if the section name itself is a keyword or part of keywords
                    if section_lower == cat_name.lower() or section_lower in keywords or any(keyword in section_lower for keyword in keywords if len(keyword) > 3):  # len >3 to avoid matching 'ai' in 'train'
                        categories_to_add_names.add(cat_name)
                        # Don't break here, a section might map to multiple relevant categories based on keywords

            # 2. Check title and description for keywords
            text_to_check = (article.title + ' ' + article.description).lower()
            for cat_name, keywords in category_keywords.items():
                if any(f' {keyword} ' in text_to_check or text_to_check.startswith(keyword + ' ') or text_to_check.endswith(' ' + keyword) for keyword in keywords):
                    categories_to_add_names.add(cat_name)

            # Create categories if they don't exist and add to article
            # Limit to a few categories (e.g., 3) to keep it manageable
            final_categories = []
            # Limit to 3 categories
            for cat_name in list(categories_to_add_names)[:3]:
                category, created = Category.objects.get_or_create(
                    name=cat_name,
                    # slugify ensures URL-friendly slug
                    defaults={'slug': slugify(cat_name)}
                )
                if created:
                    logger.info(f"Created new category: {cat_name}")
                final_categories.append(category)

            # If no specific categories found, assign to a default category
            if not final_categories:
                general_cat, created = Category.objects.get_or_create(
                    name='General News',
                    defaults={'slug': 'general-news'}
                )
                if created:
                    logger.info("Created default category: General News")
                final_categories.append(general_cat)

            # Add all collected categories
            article.categories.add(*final_categories)
            logger.info(
                f"Categorized article '{article.title}' into: {[cat.name for cat in final_categories]}")

        except Exception as e:
            logger.error(
                f"Error auto-categorizing article '{article.title}': {str(e)}")
