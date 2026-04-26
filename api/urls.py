from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import CartAPIView, CategoryViewSet, OrderViewSet, ProductReviewListCreateAPIView, ProductViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='api-products')
router.register('categories', CategoryViewSet, basename='api-categories')
router.register('orders', OrderViewSet, basename='api-orders')

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cart/', CartAPIView.as_view(), name='api-cart'),
    path('products/<int:product_id>/reviews/', ProductReviewListCreateAPIView.as_view(), name='api-product-reviews'),
    path('', include(router.urls)),
]
