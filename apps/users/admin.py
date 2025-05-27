from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
# Default Django User admin is already registered
# You can customize it here if needed, e.g., to add CustomUser if you extend AbstractUser
# admin.site.unregister(User)
# @admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin):
#     pass