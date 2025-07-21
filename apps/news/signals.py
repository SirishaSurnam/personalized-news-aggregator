# apps/news/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Article, UserActivity
from .ai_services import process_article_ai, update_user_preferences
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=Article)
def process_article_on_save(sender, instance, created, **kwargs):
    if created:
        process_article_ai.delay(instance.id)


@receiver(post_save, sender=UserActivity)
def update_user_preference_on_activity(sender, instance, created, **kwargs):
    if created:
        update_user_preferences.delay(instance.user.id)
