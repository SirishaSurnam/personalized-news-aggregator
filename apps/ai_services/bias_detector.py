from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class BiasDetector:
    def __init__(self):
        self.left_keywords = {
            "progressive": 2, "liberal": 1, "leftist": 2, 
            "climate change": 3, "social justice": 3, "renewable energy": 2,
            "racial justice": 2, "gun control": 3, "workers rights": 2
        }

        self.right_keywords = {
            "conservative": 2, "right-wing": 2, "free market": 3, 
            "gun rights": 3, "traditional values": 2, "tax cuts": 2,
            "border security": 3, "patriotism": 2, "small government": 2
        }

        self.threshold = 3  # needs weighted score >= 3

    def detect_bias(self, text):
        left_score = sum(w for k, w in self.left_keywords.items() if k in text.lower())
        right_score = sum(w for k, w in self.right_keywords.items() if k in text.lower())
        if left_score == 0 and right_score == 0:
            return "UNKNOWN"
        elif left_score >= threshold and right_score >= threshold:
            return "MIXED"
        elif left_score - right_score >= self.threshold:
            return "LEFT-LEANING"
        elif right_score - left_score >= self.threshold:
            return "RIGHT-LEANING"
        else:
            return "NEUTRAL"
