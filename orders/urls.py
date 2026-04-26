from django.urls import path

from .views import add_to_cart, cart_detail, checkout, process_payment, remove_from_cart, update_cart

urlpatterns = [
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', update_cart, name='update_cart'),
    path('checkout/', checkout, name='checkout'),
    path('payment/<int:order_id>/', process_payment, name='process_payment'),
]
