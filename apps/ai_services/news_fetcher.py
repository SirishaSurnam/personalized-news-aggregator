 import requests
import feedparser
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from apps.news.models import Article, Category # Import your models

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        self.newsapi_key = settings.NEWSAPI_KEY [cite: 52]
        self.guardian_key = settings.GUARDIAN_API_KEY [cite: 52]

    def fetch_from_source(self, source):
        """Fetch articles from specified source"""
        if source == 'newsapi': [cite: 52]
            return self.fetch_from_newsapi() [cite: 52]
        elif source == 'guardian': [cite: 52]
            return self.fetch_from_guardian() [cite: 52]
        elif source == 'rss': [cite: 52]
            return self.fetch_from_rss() [cite: 52]
        else:
            logger.error(f"Unknown source: {source}") [cite: 53]
            return 0 [cite: 53]

    def fetch_from_newsapi(self):
        """Fetch articles from NewsAPI"""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured") [cite: 53]
            return 0 [cite: 53]

        try:
            url = "https://newsapi.org/v2/top-headlines" [cite: 54]
            params = {
                'apiKey': self.newsapi_key, [cite: 54]
                'country': 'us', [cite: 54]
                'pageSize': 20, [cite: 54]
                'sortBy': 'publishedAt' [cite: 54]
            }

            response = requests.get(url, params=params, timeout=30) [cite: 55]
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx) [cite: 55]
            data = response.json() [cite: 55]

            articles_created = 0

            for item in data.get('articles', []):
                if self.create_article_from_newsapi(item): [cite: 56]
                    articles_created += 1 [cite: 56]

            logger.info(f"Created {articles_created} articles from NewsAPI") [cite: 56]
            return articles_created [cite: 56]

        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {str(e)}") [cite: 57]
            return 0 [cite: 57]

    def fetch_from_guardian(self):
        """Fetch articles from Guardian API"""
        if not self.guardian_key:
            logger.warning("Guardian API key not configured") [cite: 57]
            return 0 [cite: 57]

        try:
            url = "https://content.guardianapis.com/search" [cite: 58]
            params = {
                'api-key': self.guardian_key, [cite: 58]
                'show-fields': 'trailText,body,byline', [cite: 58]
                'page-size': 20, [cite: 58]
                'order-by': 'newest' [cite: 59]
            }

            response = requests.get(url, params=params, timeout=30) [cite: 59]
            response.raise_for_status() [cite: 59]
            data = response.json() [cite: 59]

            articles_created = 0

            for item in data.get('response', {}).get('results', []):
                if self.create_article_from_guardian(item): [cite: 60]
                    articles_created += 1 [cite: 60]

            logger.info(f"Created {articles_created} articles from Guardian") [cite: 60]
            return articles_created [cite: 61]

        except Exception as e:
            logger.error(f"Error fetching from Guardian: {str(e)}") [cite: 61]
            return 0 [cite: 61]

    def fetch_from_rss(self):
        """Fetch articles from RSS feeds"""
        rss_feeds = [
            'http://feeds.bbci.co.uk/news/rss.xml', [cite: 62]
            'http://rss.cnn.com/rss/edition.rss', [cite: 62]
            'https://feeds.reuters.com/reuters/topNews', [cite: 62]
            'https://techcrunch.com/feed/', [cite: 62]
            'https://feeds.arstechnica.com/arstechnica/index' [cite: 62]
        ]

        articles_created = 0

        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url) [cite: 63]

                for entry in feed.entries[:5]: # Limit to 5 per feed to avoid too many articles [cite: 63]
                    if self.create_article_from_rss(entry, feed_url): [cite: 63]
                        articles_created += 1 [cite: 64]

            except Exception as e:
                logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}") [cite: 64]

        logger.info(f"Created {articles_created} articles from RSS feeds") [cite: 65]
        return articles_created [cite: 65]


    def create_article_from_newsapi(self, item):
        """Create article from NewsAPI data"""
        try:
            # Skip articles without URL or title
            if not item.get('url') or not item.get('title'): [cite: 65]
                return False [cite: 66]

            # Check if article already exists to prevent duplicates
            if Article.objects.filter(url=item['url']).exists(): [cite: 66]
                return False [cite: 66]

            # Parse published date
            published_date = timezone.now()
            if item.get('publishedAt'):
                try:
                    published_date = datetime.fromisoformat(
                        item['publishedAt'].replace('Z', '+00:00')
                    ) [cite: 67]
                except ValueError: # Catch specific error for invalid date format
                    logger.warning(f"Invalid date format for NewsAPI article: {item.get('publishedAt')}") [cite: 68]
                    pass # Use timezone.now() if parsing fails

            # Create article
            article = Article.objects.create(
                title=item['title'][:500], [cite: 68]
                url=item['url'], [cite: 69]
                description=item.get('description', '')[:1000], [cite: 69]
                content=item.get('content', '')[:5000], # Limit content length [cite: 69]
                author=item.get('author', '')[:200], [cite: 69]
                source=item.get('source', {}).get('name', 'NewsAPI')[:200], [cite: 69]
                published_date=published_date [cite: 69]
            )

            # Auto-categorize based on source or content
            self.auto_categorize_article(article) [cite: 70]

            return True [cite: 70]

        except Exception as e:
            logger.error(f"Error creating article from NewsAPI: {str(e)}") [cite: 71]
            return False [cite: 71]


    def create_article_from_guardian(self, item):
        """Create article from Guardian API data"""
        try:
            if not item.get('webUrl') or not item.get('webTitle'): [cite: 71]
                return False [cite: 72]

            if Article.objects.filter(url=item['webUrl']).exists(): [cite: 72]
                return False [cite: 72]

            # Parse published date
            published_date = timezone.now()
            if item.get('webPublicationDate'):
                try:
                    published_date = datetime.fromisoformat(
                        item['webPublicationDate'].replace('Z', '+00:00')
                    ) [cite: 73]
                except ValueError:
                    logger.warning(f"Invalid date format for Guardian article: {item.get('webPublicationDate')}") [cite: 73]
                    pass # Use timezone.now() if parsing fails

            # Extract content from fields
            fields = item.get('fields', {}) [cite: 74]
            description = fields.get('trailText', '') [cite: 74]
            content = fields.get('body', '') [cite: 74]
            author = fields.get('byline', '') [cite: 74]

            # Clean HTML from content using BeautifulSoup
            if content: [cite: 75]
                soup = BeautifulSoup(content, 'html.parser') [cite: 75]
                content = soup.get_text() [cite: 75]

            article = Article.objects.create(
                title=item['webTitle'][:500], [cite: 75]
                url=item['webUrl'], [cite: 76]
                description=description[:1000], [cite: 76]
                content=content[:5000], # Limit content length [cite: 76]
                author=author[:200], [cite: 76]
                source='The Guardian', [cite: 76]
                published_date=published_date [cite: 77]
            )

            self.auto_categorize_article(article, item.get('sectionName', '')) [cite: 77]

            return True [cite: 77]

        except Exception as e:
            logger.error(f"Error creating article from Guardian: {str(e)}") [cite: 78]
            return False [cite: 78]

    def create_article_from_rss(self, entry, feed_url):
        """Create article from RSS entry"""
        try:
            if not entry.get('link') or not entry.get('title'): [cite: 78]
                return False [cite: 79]

            if Article.objects.filter(url=entry['link']).exists(): [cite: 79]
                return False [cite: 79]

            # Parse published date
            published_date = timezone.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed: [cite: 79]
                try:
                    published_date = datetime(*entry.published_parsed[:6]) [cite: 80]
                    published_date = timezone.make_aware(published_date) # Make it timezone-aware [cite: 80]
                except Exception as e:
                    logger.warning(f"Invalid date format for RSS article ({feed_url}): {entry.get('published_parsed')} - {e}") [cite: 80]
                    pass # Use timezone.now() if parsing fails

            # Determine source from feed URL
            source = self.get_source_from_url(feed_url) [cite: 81]

            # Get description
            description = ''
            if hasattr(entry, 'summary'):
                # Clean HTML from RSS summary if present
                description = BeautifulSoup(entry.summary, 'html.parser').get_text() [cite: 82]

            article = Article.objects.create(
                title=entry.title[:500], [cite: 82]
                url=entry.link, [cite: 82]
                description=description[:1000], [cite: 82]
                content='', # RSS usually doesn't provide full content in summary [cite: 82]
                author=getattr(entry, 'author', '')[:200], [cite: 83]
                source=source, [cite: 83]
                published_date=published_date [cite: 83]
            )

            self.auto_categorize_article(article) [cite: 83]

            return True [cite: 84]

        except Exception as e:
            logger.error(f"Error creating article from RSS: {str(e)}") [cite: 84]
            return False [cite: 84]

    def get_source_from_url(self, url):
        """Extract source name from feed URL"""
        if 'bbc' in url: [cite: 85]
            return 'BBC News' [cite: 85]
        elif 'cnn' in url: [cite: 85]
            return 'CNN' [cite: 85]
        elif 'reuters' in url: [cite: 85]
            return 'Reuters' [cite: 85]
        elif 'techcrunch' in url: [cite: 85]
            return 'TechCrunch' [cite: 85]
        elif 'arstechnica' in url: [cite: 85]
            return 'Ars Technica' [cite: 85]
        else:
            return 'RSS Feed' [cite: 86]

    def auto_categorize_article(self, article, section=None):
        """Automatically categorize article based on content or section"""
        try:
            categories_to_add = []

            # Category mapping (keywords are case-insensitive)
            category_keywords = {
                'Technology': ['tech', 'software', 'computer', 'internet', 'digital', 'ai', 'artificial intelligence', 'gadget', 'startup'], [cite: 87]
                'Politics': ['election', 'government', 'congress', 'senate', 'political', 'policy', 'president', 'vote'], [cite: 87]
                'Business': ['business', 'economy', 'market', 'finance', 'stock', 'company', 'invest', 'trade', 'economy'], [cite: 87]
                'Sports': ['sport', 'football', 'basketball', 'soccer', 'game', 'player', 'team', 'match'], [cite: 87]
                'Health': ['health', 'medical', 'hospital', 'doctor', 'medicine', 'disease', 'wellness', 'covid'], [cite: 88]
                'Science': ['science', 'research', 'study', 'discovery', 'scientist', 'space', 'biology', 'physics'], [cite: 88]
                'Entertainment': ['entertainment', 'movie', 'film', 'celebrity', 'music', 'tv', 'hollywood', 'art'], [cite: 88]
                'World News': ['world', 'international', 'global', 'country', 'geopolitics', 'conflict', 'diplomacy'], [cite: 88]
                'Local News': ['local', 'city', 'community', 'town', 'neighborhood'] # Added as an example
            }

            # Check section first (from Guardian API usually)
            if section: [cite: 89]
                section_lower = section.lower() [cite: 89]
                for cat_name, keywords in category_keywords.items():
                    if any(keyword in section_lower for keyword in keywords):
                        categories_to_add.append(cat_name) [cite: 90]
                        break # Add only the first matching section category

            # Check title and description for keywords
            text_to_check = (article.title + ' ' + article.description).lower() [cite: 91]

            for cat_name, keywords in category_keywords.items():
                if any(keyword in text_to_check for keyword in keywords):
                    if cat_name not in categories_to_add: # Avoid duplicates
                        categories_to_add.append(cat_name) [cite: 91]


            # Create categories if they don't exist and add to article
            for cat_name in categories_to_add[:2]: # Limit to 2 categories for primary focus [cite: 92]
                category, created = Category.objects.get_or_create(
                    name=cat_name,
                    defaults={'slug': slugify(cat_name)} [cite: 93]
                )
                article.categories.add(category) [cite: 93]

            # Default category if no specific categories found
            if not categories_to_add: [cite: 94]
                general_cat, created = Category.objects.get_or_create(
                    name='General News', [cite: 94]
                    defaults={'slug': 'general-news'} [cite: 94]
                )
                article.categories.add(general_cat) [cite: 94]

        except Exception as e:
            logger.error(f"Error auto-categorizing article: {str(e)}") [cite: 95]
