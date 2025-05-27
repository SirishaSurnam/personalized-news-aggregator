 import google.generativeai as genai
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY) [cite: 39]
            self.model = genai.GenerativeModel('gemini-pro') [cite: 39]
        else:
            self.model = None [cite: 39]
            logger.warning("Gemini API key not configured") [cite: 39]

    def summarize_article(self, content):
        """Generate a concise summary of the article"""
        if not self.model or not content:
            return "Summary not available" [cite: 40]

        try:
            # Limit content to avoid API token limits and improve performance
            prompt = f"""
            Summarize this news article in 2-3 clear, concise sentences that capture the main points: [cite: 40]

            {content[:2000]} [cite: 40]

            Focus on the key facts and main message. [cite: 41]
            Make it easy to understand. [cite: 41]
            """

            response = self.model.generate_content(prompt) [cite: 41]
            summary = response.text.strip() [cite: 42]

            # Basic validation
            if len(summary) < 10:
                return "Summary not available" [cite: 42]

            return summary [cite: 42]

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}") [cite: 42]
            return "Summary not available" [cite: 42]

    def detect_bias(self, content):
        """Detect political bias in the article"""
        if not self.model or not content:
            return 'UNKNOWN' [cite: 43]

        try:
            # Limit content to avoid API token limits
            prompt = f"""
            Analyze the political bias of this news article and classify it as one of: [cite: 43]

            - LEFT: Shows liberal/progressive bias or perspective [cite: 44]
            - RIGHT: Shows conservative bias or perspective [cite: 44]
            - NEUTRAL: Balanced, objective reporting without clear political lean [cite: 44]

            Consider the language used, sources quoted, framing of issues, and overall tone. [cite: 45]
            Article content: {content[:2000]} [cite: 45]

            Respond with only ONE WORD: LEFT, RIGHT, or NEUTRAL [cite: 45]
            """

            response = self.model.generate_content(prompt) [cite: 46]
            bias = response.text.strip().upper() [cite: 46]

            # Validate response
            if bias in ['LEFT', 'RIGHT', 'NEUTRAL']:
                return bias [cite: 46]
            else:
                return 'UNKNOWN' # Default to unknown if unclear, not neutral [cite: 46]

        except Exception as e:
            logger.error(f"Error detecting bias: {str(e)}") [cite: 47]
            return 'UNKNOWN' [cite: 47]

    def categorize_article(self, title, description):
        """Suggest categories for the article"""
        if not self.model:
            return [] [cite: 47]

        try:
            prompt = f"""
            Based on this article title and description, suggest the most relevant categories from this list: [cite: 48]
            Technology, Politics, Business, Sports, Health, Science, Entertainment, World News, Local News [cite: 48]

            Title: {title}
            Description: {description} [cite: 49]

            Return only the category names, separated by commas. [cite: 50]
            Maximum 3 categories. [cite: 50]
            """

            response = self.model.generate_content(prompt) [cite: 50]
            categories = [cat.strip() for cat in response.text.split(',')] [cite: 50]
            return categories[:3] # Limit to 3 categories [cite: 50]

        except Exception as e:
            logger.error(f"Error categorizing article: {str(e)}") [cite: 51]
            return [] [cite: 51]
