# apps/ai_services/bias_detector.py (new file)
# You can also use AutoModelForSequenceClassification and AutoTokenizer directly
# by accessing them via the pipeline object without importing them explicitly:
# model = bias_pipeline.model
# tokenizer = bias_pipeline.tokenizer
# inputs = tokenizer(text, return_tensors="pt")
# outputs = model(**inputs)
# You can then process outputs for bias detection.

# The pipeline approach (used below) is simpler for most use cases.

from transformers import pipeline


class BiasDetector:
    def __init__(self):
        self.model_name = "roberta-base-openai-detector"
        self.bias_pipeline = pipeline(
            "text-classification",
            model=self.model_name
        )

    def detect_bias(self, text):
        results = self.bias_pipeline(text)
        return results[0]['label']
