from django.contrib import admin, messages
from django.db.models import Sum

from .models import Order, OrderItem


@admin.action(description='Mark selected as Paid')
def mark_as_paid(modeladmin, request, queryset):
    updated = queryset.update(status='paid')
    modeladmin.message_user(request, f'{updated} order(s) marked as paid.', messages.SUCCESS)


@admin.action(description='Mark selected as Shipped')
def mark_as_shipped(modeladmin, request, queryset):
    updated = queryset.update(status='shipped')
    modeladmin.message_user(request, f'{updated} order(s) marked as shipped.', messages.SUCCESS)


@admin.action(description='Mark selected as Delivered')
def mark_as_delivered(modeladmin, request, queryset):
    updated = queryset.update(status='delivered')
    modeladmin.message_user(request, f'{updated} order(s) marked as delivered.', messages.SUCCESS)


@admin.action(description='Mark selected as Cancelled')
def mark_as_cancelled(modeladmin, request, queryset):
    updated = queryset.update(status='cancelled')
    modeladmin.message_user(request, f'{updated} order(s) marked as cancelled.', messages.WARNING)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')
    autocomplete_fields = []


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'status', 'formatted_total', 'items_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'user')
    ordering = ('-created_at',)
    actions = [mark_as_paid, mark_as_shipped, mark_as_delivered, mark_as_cancelled]
    inlines = [OrderItemInline]
    change_list_template = 'admin/orders/order/change_list.html'
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'status', 'total_price'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Customer Email')
    def user_email(self, obj):
        return obj.user.email if obj.user else '—'

    @admin.display(description='Total')
    def formatted_total(self, obj):
        return f'${obj.total_price:.2f}'

    @admin.display(description='Items')
    def items_count(self, obj):
        return obj.items.count()

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        # Use the changelist queryset so analytics respect active filters/search.
        if hasattr(response, 'context_data') and response.context_data.get('cl'):
            queryset = response.context_data['cl'].queryset
            stats = queryset.aggregate(total_revenue=Sum('total_price'))
            response.context_data['total_orders'] = queryset.count()
            response.context_data['total_revenue'] = stats.get('total_revenue') or 0

        return response
