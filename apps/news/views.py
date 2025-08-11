from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Article, Category, Bookmark, UserInterest
from .serializers import ArticleSerializer
from .tasks import process_article_ai


from django.views.decorators.csrf import csrf_exempt

from .tasks import fetch_latest_news
import json


def home(request):
    articles = Article.objects.all()

    if request.user.is_authenticated:
        user_categories = UserInterest.objects.filter(
            user=request.user).values_list('category', flat=True)
        if user_categories:
            articles = articles.filter(
                categories__in=user_categories).distinct()

    search_query = request.GET.get('search', '')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    bias_filter = request.GET.get('bias', '')
    if bias_filter:
        articles = articles.filter(bias_score=bias_filter)

    category_filter = request.GET.get('category', '')
    if category_filter:
        articles = articles.filter(categories__slug=category_filter)

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    bookmarked_articles = []
    if request.user.is_authenticated:
        bookmarked_articles = list(Bookmark.objects.filter(
            user=request.user).values_list('article_id', flat=True))

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'search_query': search_query,
        'bias_filter': bias_filter,
        'category_filter': category_filter,
        'bookmarked_articles': bookmarked_articles,
        'bias_choices': Article.BIAS_CHOICES,
    }
    return render(request, 'home.html', context)


def article_detail(request, id):
    article = get_object_or_404(Article, id=id)
    is_bookmarked = False

    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(
            user=request.user, article=article).exists()

    if not article.summary or article.bias_score == 'UNKNOWN':
        process_article_ai.delay(article.id)

    context = {
        'article': article,
        'is_bookmarked': is_bookmarked,
    }
    return render(request, 'article_detail.html', context)


@login_required
@require_POST
def toggle_bookmark(request):
    article_id = request.POST.get('article_id')
    article = get_object_or_404(Article, id=article_id)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        article=article
    )

    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True

    return JsonResponse({'bookmarked': bookmarked})


@login_required
def bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user)
    paginator = Paginator(bookmarks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'bookmarks.html', context)


@login_required
def profile(request):
    user_interests = UserInterest.objects.filter(user=request.user)
    all_categories = Category.objects.all()

    if request.method == 'POST':
        selected_categories = request.POST.getlist('categories')

        UserInterest.objects.filter(user=request.user).delete()

        for category_id in selected_categories:
            category = get_object_or_404(Category, id=category_id)
            UserInterest.objects.create(user=request.user, category=category)

        messages.success(request, 'Your interests have been updated!')
        return redirect('profile')

    context = {
        'user_interests': user_interests,
        'all_categories': all_categories,
        'selected_categories': list(
            user_interests.values_list('category_id', flat=True)
        ),
    }
    return render(request, 'profile.html', context)


class ArticleListAPI(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = Article.objects.all()

        if self.request.user.is_authenticated:
            user_categories = UserInterest.objects.filter(
                user=self.request.user).values_list('category', flat=True)
            if user_categories:
                queryset = queryset.filter(
                    categories__in=user_categories).distinct()

        bias = self.request.query_params.get('bias')
        if bias:
            queryset = queryset.filter(bias_score=bias)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(categories__slug=category)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset



@login_required
def dashboard(request):
    # Get user interests
    user_categories = UserInterest.objects.filter(
        user=request.user
    ).values_list('category', flat=True)

    # Start with articles from those categories
    articles = Article.objects.filter(
        categories__in=user_categories
    ).distinct()

    # Filters from request
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    bias_filter = request.GET.get('bias', '')

    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_filter:
        articles = articles.filter(categories__slug=category_filter)
    '''
    if bias_filter:
        articles = articles.filter(bias_score=bias_filter)
    '''

    print(f"Bias filter selected: '{bias_filter}'")
    print(f"Articles before bias filter: {articles.count()}")
    if bias_filter:
        articles = articles.filter(bias_score=bias_filter)
        print(f"Articles after bias filter: {articles.count()}")


    bias_choices = Article.BIAS_CHOICES
    
    ''' 
    if bias_filter:
    

    # Get only the bias options that actually exist in DB
    available_bias = (
        Article.objects
        .exclude(bias_score__isnull=True)
        .exclude(bias_score='')
        .exclude(bias_score='UNKNOWN')  # exclude unknown from filter
        .values_list('bias_score', flat=True)
        .distinct()
    )
    
    bias_choices = [
        (code, label)
        for code, label in Article.BIAS_CHOICES
        if code in available_bias
    ]

    bias_choices = [
        (code, label)
        for code, label in Article.BIAS_CHOICES
        if code.strip().upper() in [b.upper() for b in available_bias]
    ]
    ''' 
    # Pagination
    paginator = Paginator(articles, 9)  # 9 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'bias_filter': bias_filter,
        'categories': Category.objects.all(),
        'bias_choices': bias_choices,
    })


'''
# apps/news/views.py
# from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    user_categories = UserInterest.objects.filter(
        user=request.user).values_list('category', flat=True)
    articles = Article.objects.filter(
        categories__in=user_categories).distinct()

    search_query = request.GET.get('search', '')
    if search_query:
        articles = articles.filter(Q(title__icontains=search_query) | Q(
            description__icontains=search_query))

    bias_filter = request.GET.get('bias', '')
    if bias_filter:
        articles = articles.filter(bias_score=bias_filter)
    


    # Fetch distinct bias values present in DB
    available_bias = (
        Article.objects
        .exclude(bias_score__isnull=True)
        .exclude(bias_score='')
        .values_list('bias_score', flat=True)
        .distinct()
    )

    # Map them to human-readable labels (from model choices)
    bias_choices = [
        (code, label)
        for code, label in Article.BIAS_CHOICES
        if code in available_bias
    ]


    # Pagination (if you already have it)
    from django.core.paginator import Paginator
    paginator = Paginator(articles, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'bias_filter': bias_filter,
        'categories': Category.objects.all(),
        'bias_choices': bias_choices,  # <-- pass filtered bias list
    })



    category_filter = request.GET.get('category', '')
    if category_filter:
        articles = articles.filter(categories__slug=category_filter)

    paginator = Paginator(articles, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'search_query': search_query,
        'bias_filter': bias_filter,
        'category_filter': category_filter,
    }
    return render(request, 'dashboard.html', context)

'''








@csrf_exempt
def fetch_missing_summaries(request):
    if request.method == 'POST':
        article_ids = request.POST.getlist('article_ids[]')
        triggered = []

        for article_id in article_ids[:5]:
            try:
                article = Article.objects.get(id=article_id)
                if not article.summary:
                    # 🟧 Assign to medium queue
                    process_article_ai.apply_async(
                        args=[article.id], queue='medium')
                    triggered.append(article.id)
            except Article.DoesNotExist:
                continue

        return JsonResponse({'status': 'success', 'triggered': triggered})

    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def fetch_summary_for_article(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        try:
            article = Article.objects.get(id=article_id)
            if not article.summary:
                # 🟥 Assign to high priority queue here
                process_article_ai.apply_async(args=[article.id], queue='high')
                return JsonResponse({'status': 'triggered'})
        except Article.DoesNotExist:
            pass

    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@require_POST
def refresh_and_redirect(request):
    try:
        fetch_latest_news.delay()  # run celery task
        return JsonResponse({"status": "success", "message": "News refresh triggered."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

'''
# Updated refresh function for web interface
@csrf_exempt
@require_POST
def refresh_and_redirect_web(request):
    """Web interface refresh - returns JSON response for AJAX"""
    try:
        from .tasks import fetch_latest_news
        fetch_latest_news.delay()
        return JsonResponse({
            'status': 'success',
            'message': '📰 News refresh started! Please wait a few seconds.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to start news refresh. Please try again.'
        }, status=500)

# Keep your existing API function for API endpoints
@api_view(['POST'])
def refresh_articles(request):
    """API endpoint for refresh"""
    try:
        from .tasks import fetch_latest_news
        fetch_latest_news.delay()
        return Response(
            {'message': 'News refresh started'},
            status=status.HTTP_202_ACCEPTED
        )
    except Exception as e:
        return Response(
            {'message': 'Failed to start news refresh'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt  # Optional if you handle CSRF via JS
@require_POST
def refresh_and_redirect(request):
    try:
        # Trigger Celery task
        fetch_latest_news.apply_async(queue='default')

        return JsonResponse({
            "status": "success",
            "message": "News refresh triggered."
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

# Alternative: You can also modify your existing refresh_and_redirect function
def refresh_and_redirect(request):
    """Original redirect-based refresh function"""
    try:
        from .tasks import fetch_latest_news
        fetch_latest_news.delay()
        messages.success(request, "📰 News refresh started! Please wait a few seconds.")
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': '📰 News refresh started! Please wait a few seconds.'
            })
        
        return redirect('home')  # Regular redirect for non-AJAX requests
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to start news refresh'
            }, status=500)
        
        messages.error(request, "Failed to refresh news. Please try again.")
        return redirect('home')
'''

@api_view(['POST'])
def refresh_articles(request):
    from .tasks import fetch_latest_news
    fetch_latest_news.delay()
    return Response(
        {'message': 'News refresh started'},
        status=status.HTTP_202_ACCEPTED
    )
'''
    def refresh_and_redirect(request):
    from .tasks import fetch_latest_news
    fetch_latest_news.delay()
    messages.success(request, "📰 News refresh started! Please wait a few seconds.")
    return redirect('home')  # or 'dashboard' if you want
'''





from .chatbot import GeminiNewsChatbot

@csrf_exempt
def chatbot_api(request):
    """Lightweight chatbot API endpoint"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'response': 'Please ask me something about news!'})
        
        # Initialize chatbot with current user
        chatbot = GeminiNewsChatbot(user=request.user)
        response = chatbot.get_response(user_message)
        
        return JsonResponse({
            'response': response,
            'status': 'success'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Chatbot API error: {str(e)}")
        return JsonResponse({
            'response': 'Sorry, I encountered an error. Please try again!',
            'status': 'error'
        })