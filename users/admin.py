from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Address

User = get_user_model()


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'postal_code', 'is_default')
    list_filter = ('is_default', 'city')
    search_fields = ('user__username', 'full_name', 'phone', 'city', 'address_line', 'postal_code')
    ordering = ('user__username',)


if not admin.site.is_registered(User):
    @admin.register(User)
    class UserAdmin(BaseUserAdmin):
        list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
        list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
        search_fields = ('username', 'email', 'first_name', 'last_name')
        ordering = ('-date_joined',)
