# File: apps/ai_services/bias_detector.py
from transformers import pipeline


class BiasDetector:
    def __init__(self):
        self.model_name = "joeddav/distilbert-base-uncased-go-emotions-student"
        self.bias_pipeline = pipeline(
            "zero-shot-classification",
            model=self.model_name
        )

    def detect_bias(self, text):
        """Detect political bias in the article"""
        if not self.model or not text:
            return 'UNKNOWN'

        try:
            # ✅ Move hypothesis_template here
            result = self.bias_pipeline(
                text,
                candidate_labels=["LEFT", "RIGHT", "NEUTRAL"],
                hypothesis_template="This text expresses {} bias."
            )
            bias = result['labels'][0]  # highest probability

            # Validate response
            if bias in ['LEFT', 'RIGHT', 'NEUTRAL']:
                return bias
            else:
                return 'UNKNOWN'

        except Exception as e:
            logger.error(f"Error detecting bias: {str(e)}")
            return 'UNKNOWN'
