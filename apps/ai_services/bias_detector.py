from transformers import pipeline
import logging

logger = logging.getLogger(__name__)


class BiasDetector:
    def __init__(self):
        self.model_name = "joeddav/distilbert-base-uncased-go-emotions-student"
        self.bias_pipeline = pipeline(
            "zero-shot-classification",
            model=self.model_name
        )

    def detect_bias(self, text):
        """Detect political bias in the article"""
        if not text:
            return 'UNKNOWN'

        try:
            result = self.bias_pipeline(
                text,
                candidate_labels=["LEFT", "RIGHT", "NEUTRAL"],
                hypothesis_template="This text expresses {} bias."
            )
            bias = result['labels'][0]  # highest confidence
            return bias if bias in ['LEFT', 'RIGHT', 'NEUTRAL'] else 'UNKNOWN'

        except Exception as e:
            logger.error(f"[BiasDetector] Error: {str(e)}")
            return 'UNKNOWN'
