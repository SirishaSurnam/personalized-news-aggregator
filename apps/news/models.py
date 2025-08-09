from django.db import models
from django.contrib.auth.models import User  # Django's built-in User model
from django.utils.text import slugify
from apps.ai_services import CachedSummarizer, BiasDetector


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
    summary = models.TextField(blank=True, null=True)  # AI-generated summary
    content = models.TextField(blank=True)
    author = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=200, db_index=True)
    published_date = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_url = models.URLField(blank=True, null=True)  # image URL

    # AI-generated fields
    summary = models.TextField(blank=True)
    bias_score = models.CharField(
        max_length=10,
        choices=BIAS_CHOICES,
        default='UNKNOWN',
        db_index=True
    )

    # Relationships
    categories = models.ManyToManyField(Category, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
        # Returns a color code based on bias_score
        return {
            'LEFT': '#3498db',      # blue
            'RIGHT': '#e74c3c',     # red
            'NEUTRAL': '#2ecc71',   # green
            'UNKNOWN': '#95a5a6',   # grey
        }.get(self.bias_score, '#95a5a6')

    @property
    def get_bias_score_display(self):
        bias_labels = {
            'left': 'Left Bias',
            'center': 'Center',
            'right': 'Right Bias',
            'unknown': 'Unknown'
        }
        return bias_labels.get(self.bias_score, 'Unknown')

    def save(self, *args, **kwargs):
        if not self.summary:
            from apps.ai_services import CachedSummarizer
            summarizer = CachedSummarizer()
            self.summary = summarizer.summarize(
                self.content or self.description)
        super().save(*args, **kwargs)

    def _generate_ai_content(self):
        try:
            summarizer = CachedSummarizer()
            self.summary = summarizer.summarize(self.content)

            bias_detector = BiasDetector()
            self.bias_score = bias_detector.detect_bias(self.content)

        except Exception as e:
            print(f"AI processing failed for article {self.id}: {e}")
            self.summary = self.description[:200] + "..."
            self.bias_score = 'UNKNOWN'


class UserInterest(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='interests'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'category']

    def __str__(self):
        return f"{self.user.username} - {self.category.name}"


class Bookmark(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='bookmarked_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'article']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.article.title[:50]}"


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey('Article', on_delete=models.CASCADE)
    action = models.CharField(max_length=20)  # 'read', 'bookmark', 'search'
    timestamp = models.DateTimeField(auto_now_add=True)
    search_query = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return (
            f"{self.user.username} - {self.action} - "
            f"{self.article.title[:50]}"
        )
