from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.db.models import QuerySet
from django.views.generic import ListView, DetailView

from reviews.models import Review

from .models import Category, Product

SORT_OPTIONS = {
    'price_asc': 'price',
    'price_desc': '-price',
    'newest': '-created_at',
}


class HomeView(ListView):
    """Product listing with filtering by category/search and price range, plus sorting."""
    model = Product
    template_name = 'home.html'
    context_object_name = 'products'
    paginate_by = 9

    def get_queryset(self) -> QuerySet[Product]:
        qs = Product.objects.filter(is_active=True)

        # Category filter
        categories = self.request.GET.getlist('category')
        if categories:
            qs = qs.filter(category__slug__in=categories)

        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        # Price range
        min_price_raw = self.request.GET.get('min_price', '').strip()
        max_price_raw = self.request.GET.get('max_price', '').strip()

        if min_price_raw:
            try:
                min_price = Decimal(min_price_raw)
            except (InvalidOperation, ValueError):
                min_price = None
            if min_price is not None:
                qs = qs.filter(price__gte=min_price)

        if max_price_raw:
            try:
                max_price = Decimal(max_price_raw)
            except (InvalidOperation, ValueError):
                max_price = None
            if max_price is not None:
                qs = qs.filter(price__lte=max_price)

        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        order = SORT_OPTIONS.get(sort, '-created_at')
        qs = qs.order_by(order)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['selected_categories'] = self.request.GET.getlist('category')
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_sort'] = self.request.GET.get('sort', 'newest')
        ctx['current_min_price'] = self.request.GET.get('min_price', '')
        ctx['current_max_price'] = self.request.GET.get('max_price', '')
        ctx['featured_products'] = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
        return ctx


class ProductDetailView(DetailView):
    """Display single product with details, reviews, and review creation form."""
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        reviews = Review.objects.filter(product=product).select_related('user').order_by('-created_at')
        context['reviews'] = reviews
        return context
