# config/caching.py
from django.core.cache import cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# apps/ai_services/__init__.py


class CachedSummarizer(OptimizedSummarizer):
    def summarize(self, text, max_length=100):
        cache_key = f'summary_{hash(text[:1000])}'  # Hash first 1000 chars
        cached_summary = cache.get(cache_key)

        if cached_summary:
            return cached_summary

        summary = super().summarize(text, max_length)
        cache.set(cache_key, summary, 3600)  # Cache for 1 hour
        return summary
