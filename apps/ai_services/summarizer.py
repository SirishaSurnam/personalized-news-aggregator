# apps/ai_services/summarizer.py (optimized)
from transformers import pipeline
import torch


class OptimizedSummarizer:
    def __init__(self):
        # Use smaller, faster models
        self.model = "google/flan-t5-small"
        # "sshleifer/distilbart-cnn-12-6"
        # "google/flan-t5-small"  # Faster than flan-t5-large

        self.device = 0 if torch.cuda.is_available() else -1
        self._summarizer = None

    @property
    def summarizer(self):
        if self._summarizer is None:
            self._summarizer = pipeline(
                "summarization",
                model=self.model,
                device=self.device
            )
        return self._summarizer

    def summarize(self, text, max_length=100):
        if len(text) < 500:  # Skip summarization for short texts
            return text[:200] + "..."

        return self.summarizer(
            text,
            max_length=max_length,
            min_length=30,
            do_sample=False,
            truncation=True
        )[0]['summary_text']
