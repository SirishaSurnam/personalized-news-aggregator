# apps/ai_services/__init__.py
from config.caching import CachedSummarizer
from .summarizer import OptimizedSummarizer  # Changed from AdvancedSummarizer
from .bias_detector import BiasDetector
from .personalizer import NewsPersonalizer

__all__ = ['OptimizedSummarizer', 'BiasDetector',
           'NewsPersonalizer']  # Updated
