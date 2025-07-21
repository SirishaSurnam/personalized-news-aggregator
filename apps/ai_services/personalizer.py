# apps/ai_services/personalizer.py (new file)
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class NewsPersonalizer:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_user_profile(self, user):
        articles = user.read_articles.all()
        article_texts = [
            f"{article.title} {article.description}" for article in articles]
        embeddings = self.embedding_model.encode(article_texts)
        return np.mean(embeddings, axis=0)

    def recommend_articles(self, user, articles, top_n=10):
        user_profile = self.generate_user_profile(user)
        article_texts = [
            f"{article.title} {article.description}" for article in articles]
        article_embeddings = self.embedding_model.encode(article_texts)

        similarities = cosine_similarity([user_profile], article_embeddings)[0]
        ranked_indices = np.argsort(similarities)[::-1][:top_n]

        return [articles[i] for i in ranked_indices]
