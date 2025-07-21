# apps/ai_services/summarizer.py (optimized)
from transformers import pipeline
import torch


class OptimizedSummarizer:
    # Use smaller, faster models
    # self.model_name = "facebook/bart-large-mnli"
    # "google/flan-t5-small"
    # "sshleifer/distilbart-cnn-12-6"
    # "google/flan-t5-small"  # Faster than flan-t5-large

    def __init__(self):
        self.model = "google/flan-t5-small"
        self.device = 0 if torch.cuda.is_available() else -1
        self._summarizer = pipeline(
            "summarization",
            model=self.model,
            device=self.device
        )

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
