from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'product', 'star_rating', 'short_comment', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'user__email', 'product__name', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    autocomplete_fields = ['product']
    fieldsets = (
        ('Review', {
            'fields': ('user', 'product', 'rating', 'comment'),
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email if obj.user else '—'

    @admin.display(description='Rating')
    def star_rating(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)

    @admin.display(description='Comment')
    def short_comment(self, obj):
        return (obj.comment[:60] + '…') if obj.comment and len(obj.comment) > 60 else obj.comment
