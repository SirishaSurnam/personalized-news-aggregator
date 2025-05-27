from django.db import models
from django.contrib.auth.models import User # Django's built-in User model
from django.utils import timezone
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Article(models.Model):
    BIAS_CHOICES = [
        ('LEFT', 'Left-leaning'),
        ('RIGHT', 'Right-leaning'),
        ('NEUTRAL', 'Neutral'),
        ('UNKNOWN', 'Unknown'),
    ]
    title = models.CharField(max_length=500, db_index=True)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    author = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=200, db_index=True)
    published_date = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # AI-generated fields
    summary = models.TextField(blank=True)
    bias_score = models.CharField(max_length=10, choices=BIAS_CHOICES, default='UNKNOWN', db_index=True)

    # Relationships
    categories = models.ManyToManyField(Category, blank=True)

    class Meta:
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['published_date', 'bias_score']),
            models.Index(fields=['source', 'published_date']),
        ]
    
    def __str__(self):
        return self.title[:100]

    @property
    def bias_color(self):
        return {
            'LEFT': 'primary',
            'RIGHT': 'danger',
            'NEUTRAL': 'success',
            'UNKNOWN': 'secondary'
        }.get(self.bias_score, 'secondary')

class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interests')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'category']

    def __str__(self):
        return f"{self.user.username} - {self.category.name}"

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'article']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.article.title[:50]}"