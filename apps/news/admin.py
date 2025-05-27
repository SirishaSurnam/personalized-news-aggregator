from django.contrib import admin
from .models import Category, Article, UserInterest, Bookmark

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'bias_score', 'published_date', 'created_at']
    list_filter = ['bias_score', 'source', 'published_date', 'categories']
    search_fields = ['title', 'description', 'author']
    filter_horizontal = ['categories']
    date_hierarchy = 'published_date'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['user__username', 'category__name']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'article__title']