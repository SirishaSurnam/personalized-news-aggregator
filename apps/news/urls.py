from django.urls import path
from . import views  # Import views from the current app
# from apps.news.views import refresh_and_redirect

urlpatterns = [
    path('', views.home, name='home'),  # Main home page
    path('article/<int:id>/', views.article_detail, name='article_detail'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('profile/', views.profile, name='profile'),
    path('toggle-bookmark/', views.toggle_bookmark, name='toggle_bookmark'),

    # API endpoints
    path('articles/', views.ArticleListAPI.as_view(), name='api_articles'),
    path('refresh-news/', views.refresh_articles, name='refresh_articles'),
    # path("refresh-news/", views.refresh_and_redirect, name="refresh_news"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('fetch_summaries/', views.fetch_missing_summaries,
         name='fetch_missing_summaries'),

]
