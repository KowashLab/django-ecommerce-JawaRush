from django.contrib import admin
from django.db.models import Sum

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'status', 'payment_method', 'total_price', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username',)
    inlines = [OrderItemInline]

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        stats = qs.aggregate(total_revenue=Sum('total_price'))
        extra_context = extra_context or {}
        extra_context['total_orders'] = qs.count()
        extra_context['total_revenue'] = stats['total_revenue'] or 0
        return super().changelist_view(request, extra_context=extra_context)
