from transformers import pipeline
import logging

logger = logging.getLogger(__name__)


class BiasDetector:
    def __init__(self):
        self.bias_keywords = {
            "left": ["progressive", "liberal", "leftist", "climate change", "social justice"],
            "right": ["conservative", "right-wing", "free market", "gun rights", "traditional values"]
        }
        self.bias_threshold = 1  # Lowered from 2 to detect more subtle bias

    def detect_bias(self, text):
        if not text or len(text.strip()) < 30:
            logger.warning("⚠️ Text too short for bias detection. Returning UNKNOWN.")
            return "UNKNOWN"

        text_lower = text.lower()
        left_score = sum(kw in text_lower for kw in self.bias_keywords["left"])
        right_score = sum(kw in text_lower for kw in self.bias_keywords["right"])

        logger.info(f"Bias Detection: LEFT={left_score}, RIGHT={right_score}, Text length={len(text)}")

        if left_score > right_score:
            return "LEFT-LEANING"
        elif right_score > left_score:
            return "RIGHT-LEANING"
        elif left_score == right_score and left_score > 0:
            return "MIXED"
        else:
            return "NEUTRAL"

'''
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
'''