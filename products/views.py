from django.db.models import Q
from django.views.generic import ListView, DetailView

from .models import Category, Product

SORT_OPTIONS = {
    'price_asc': 'price',
    'price_desc': '-price',
    'newest': '-created_at',
}


class HomeView(ListView):
    model = Product
    template_name = 'home.html'
    context_object_name = 'products'
    paginate_by = 9

    def get_queryset(self):
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
        ctx['featured_products'] = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
