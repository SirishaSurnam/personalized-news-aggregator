

from transformers import pipeline


class BiasDetector:
    def __init__(self):
        self.model_name = "facebook/bart-large-mnli"  # ✅ safer and supports longer input
        self.bias_pipeline = pipeline(
            "zero-shot-classification",
            model=self.model_name
        )

    def detect_bias(self, text):
        candidate_labels = ["LEFT", "RIGHT", "NEUTRAL"]
        result = self.bias_pipeline(text, candidate_labels)
        return result['labels'][0]  # highest probability
