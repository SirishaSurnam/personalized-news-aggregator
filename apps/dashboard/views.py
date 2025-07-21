# apps/dashboard/views.py
from django.views.generic import ListView
from ..news.models import Article, Category
from ..ai_services.personalizer import NewsPersonalizer


class DashboardView(ListView):
    model = Article
    template_name = 'dashboard.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        articles = Article.objects.select_related(
            'source').prefetch_related('categories')

        # Apply filters
        search_query = self.request.GET.get('search')
        category_filter = self.request.GET.get('category')
        bias_filter = self.request.GET.get('bias')

        if search_query:
            articles = articles.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if category_filter:
            articles = articles.filter(categories__slug=category_filter)

        if bias_filter:
            articles = articles.filter(bias_score=bias_filter)

        # Apply personalization
        if self.request.user.is_authenticated:
            articles = self._apply_personalization(articles)

        return articles

    def _apply_personalization(self, articles):
        try:
            personalizer = NewsPersonalizer()
            return personalizer.recommend_articles(self.request.user, articles)
        except Exception as e:
            print(f"Personalization error: {e}")
            return articles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add categories for filter dropdown
        context['categories'] = Category.objects.all()

        # Add bias choices for filter dropdown
        context['bias_choices'] = [
            ('left', 'Left Bias'),
            ('center', 'Center'),
            ('right', 'Right Bias'),
            ('unknown', 'Unknown')
        ]

        return context
