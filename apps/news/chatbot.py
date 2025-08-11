# chatbot.py - Lightweight Gemini chatbot service
import google.generativeai as genai
from django.conf import settings
import json
import logging
from .models import Article, Category, UserInterest

logger = logging.getLogger(__name__)

class GeminiNewsChatbot:
    def __init__(self, user=None):
        self.user = user
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use Gemini 1.5 Flash - fast and lightweight
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Cache for frequent queries (avoid API calls)
        self._cache = {}
        
    def get_response(self, user_message):
        """Main chatbot response handler"""
        try:
            # Check cache first for common queries
            cache_key = user_message.lower().strip()
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Build lightweight context about available news
            context = self._build_context()
            
            # Create focused prompt for news assistance
            system_prompt = f"""You are a helpful news assistant for a news aggregation platform.

AVAILABLE DATA:
{context}

USER CONTEXT:
- User interests: {self._get_user_interests()}
- Total articles: {Article.objects.count()}

INSTRUCTIONS:
- Be concise (max 2-3 sentences)
- Focus on helping find relevant news
- Suggest specific categories/topics when possible
- If asked about specific articles, reference them by title
- If asked about bias, explain the options: NEUTRAL, LEFT-LEANING, RIGHT-LEANING, MIXED

USER QUESTION: {user_message}"""

            # Generate response with Gemini Flash
            response = self.model.generate_content(
                system_prompt,
                generation_config={
                    "max_output_tokens": 150,  # Keep responses short
                    "temperature": 0.3,        # Less creative, more factual
                    "top_p": 0.8
                }
            )
            
            bot_response = response.text.strip()
            
            # Cache common responses to reduce API calls
            if len(cache_key) > 3 and any(word in cache_key for word in ['latest', 'news', 'help', 'bias']):
                self._cache[cache_key] = bot_response
                
            return bot_response
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return self._fallback_response(user_message)
    
    def _build_context(self, limit=8):
        """Build lightweight context - only essential info"""
        try:
            # Get recent articles (limit to avoid token overload)
            recent_articles = Article.objects.select_related().all()[:limit]
            
            context = "RECENT ARTICLES:\n"
            for i, article in enumerate(recent_articles, 1):
                # Keep it minimal
                bias_display = article.get_bias_score_display() if hasattr(article, 'get_bias_score_display') else article.bias_score
                context += f"{i}. {article.title[:60]}... (Bias: {bias_display})\n"
            
            # Add available categories
            categories = list(Category.objects.values_list('name', flat=True)[:6])
            context += f"\nCATEGORIES: {', '.join(categories)}\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Context building error: {str(e)}")
            return "Recent news articles are available across multiple categories."
    
    def _get_user_interests(self):
        """Get user's interests if authenticated"""
        if not self.user or not self.user.is_authenticated:
            return "Not specified"
            
        try:
            interests = UserInterest.objects.filter(user=self.user).select_related('category')
            if interests:
                return ", ".join([interest.category.name for interest in interests])
            return "Not set"
        except:
            return "Not available"
    
    def _fallback_response(self, user_message):
        """Simple fallback if Gemini fails"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['latest', 'recent', 'new']):
            articles = Article.objects.all()[:3]
            response = "📰 Latest articles:\n"
            for article in articles:
                response += f"• {article.title}\n"
            return response
            
        elif 'bias' in message_lower:
            return "I can help filter news by bias: NEUTRAL, LEFT-LEANING, RIGHT-LEANING, or MIXED. What would you prefer?"
            
        elif any(word in message_lower for word in ['help', 'what', 'how']):
            return "I can help you find news! Try asking about 'latest news', specific topics like 'technology', or bias filtering."
            
        return "I'm having trouble right now. Try asking about 'latest news' or specific topics!"


