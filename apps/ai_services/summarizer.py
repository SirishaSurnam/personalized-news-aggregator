# apps/ai_services/summarizer.py (optimized)
from transformers import pipeline
import torch


# ✅ Global model loading - once at startup
DEVICE = 0 if torch.cuda.is_available() else -1
MODEL_NAME = "google/flan-t5-small"

# ✅ Global summarizer instance (created once)
summarizer_pipeline = pipeline(
    "summarization",
    model=MODEL_NAME,
    device=DEVICE
)


class OptimizedSummarizer:
    def summarize(self, text, max_length=100):
        if len(text) < 500:
            return text[:200] + "..."

        # ✅ Use the globally loaded pipeline
        return summarizer_pipeline(
            text,
            max_length=max_length,
            min_length=30,
            do_sample=False,
            truncation=True
        )[0]['summary_text']

    # Use smaller, faster models
    # self.model_name = "facebook/bart-large-mnli"
    # "google/flan-t5-small"
    # "sshleifer/distilbart-cnn-12-6"
    # "google/flan-t5-small"  # Faster than flan-t5-large

    # apps/ai_services/summarizer.py
