from django.contrib.auth.models import AbstractUser
from django.db import models
# Using Django's default User model, but you can extend it here if needed
# class CustomUser(AbstractUser):
#     bio = models.TextField(max_length=500, blank=True)
#     birth_date = models.DateField(null=True, blank=True)