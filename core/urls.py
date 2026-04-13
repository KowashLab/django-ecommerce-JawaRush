"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from products.views import HomeView, ProductDetailView
from orders.views import cart_detail, add_to_cart, remove_from_cart, update_cart, checkout, process_payment
from users.views import register_view, login_view, logout_view, account_view, profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', update_cart, name='update_cart'),
    path('checkout/', checkout, name='checkout'),
    path('payment/<int:order_id>/', process_payment, name='process_payment'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-change/', PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password-change/done/', PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    path('account/', account_view, name='account'),
    path('account/profile/', profile_view, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
