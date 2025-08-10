from rest_framework import serializers
from .models import Article, Category, Bookmark

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ArticleSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    bias_color = serializers.ReadOnlyField()  # From @property in model

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'url', 'description', 'content', 'author',
            'source', 'published_date', 'summary', 'bias_score',
            'bias_color', 'categories' , 'image_url', 
        ]