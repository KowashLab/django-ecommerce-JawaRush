from django.contrib import admin
from django.db.models import Sum

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
    inlines = [OrderItemInline]
    change_list_template = 'admin/orders/order/change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        # Use the changelist queryset so analytics respect active filters/search.
        if hasattr(response, 'context_data') and response.context_data.get('cl'):
            queryset = response.context_data['cl'].queryset
            stats = queryset.aggregate(total_revenue=Sum('total_price'))
            response.context_data['total_orders'] = queryset.count()
            response.context_data['total_revenue'] = stats.get('total_revenue') or 0

        return response
