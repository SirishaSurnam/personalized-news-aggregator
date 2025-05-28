import google.generativeai as genai
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            logger.warning("Gemini API key not configured")

    def summarize_article(self, content):
        """Generate a concise summary of the article"""
        if not self.model or not content:
            return "Summary not available"

        try:
            # Limit content to avoid API token limits and improve performance
            prompt = f"""
            Summarize this news article in 2-3 clear, concise sentences that capture the main points:

            {content[:2000]}

            Focus on the key facts and main message.
            Make it easy to understand.
            """

            response = self.model.generate_content(prompt)
            summary = response.text.strip()

            # Basic validation
            if len(summary) < 10:
                return "Summary not available"

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Summary not available"

    def detect_bias(self, content):
        """Detect political bias in the article"""
        if not self.model or not content:
            return 'UNKNOWN'

        try:
            # Limit content to avoid API token limits
            prompt = f"""
            Analyze the political bias of this news article and classify it as one of:

            - LEFT: Shows liberal/progressive bias or perspective
            - RIGHT: Shows conservative bias or perspective
            - NEUTRAL: Balanced, objective reporting without clear political lean

            Consider the language used, sources quoted, framing of issues, and overall tone.
            Article content: {content[:2000]}

            Respond with only ONE WORD: LEFT, RIGHT, or NEUTRAL
            """

            response = self.model.generate_content(prompt)
            bias = response.text.strip().upper()

            # Validate response
            if bias in ['LEFT', 'RIGHT', 'NEUTRAL']:
                return bias
            else:
                return 'UNKNOWN'

        except Exception as e:
            logger.error(f"Error detecting bias: {str(e)}")
            return 'UNKNOWN'

    def categorize_article(self, title, description):
        """Suggest categories for the article"""
        if not self.model:
            return []

        try:
            prompt = f"""
            Based on this article title and description, suggest the most relevant categories from this list:
            Technology, Politics, Business, Sports, Health, Science, Entertainment, World News, Local News

            Title: {title}
            Description: {description}

            Return only the category names, separated by commas.
            Maximum 3 categories.
            """

            response = self.model.generate_content(prompt)
            categories = [cat.strip() for cat in response.text.split(',')]
            return categories[:3]  # Limit to 3 categories

        except Exception as e:
            logger.error(f"Error categorizing article: {str(e)}")
            return []
