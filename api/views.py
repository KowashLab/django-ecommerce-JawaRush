from django.db.models import QuerySet
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review

from .serializers import CategorySerializer, OrderSerializer, ProductSerializer, ReviewSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for active products. Supports category filtering by ID or slug."""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self) -> QuerySet[Product]:
        queryset = Product.objects.filter(is_active=True).select_related('category')
        category = self.request.query_params.get('category')
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(category__slug=category)
        return queryset.order_by('-created_at')


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for browsing product categories."""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class OrderViewSet(viewsets.ModelViewSet):
    """Authenticated endpoint for user orders. Includes custom cancel action for pending orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related('items__product')
            .order_by('-created_at')
        )

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response(
                {'detail': 'Only pending orders can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status'])
        return Response({'detail': 'Order cancelled successfully.'}, status=status.HTTP_200_OK)


class CartAPIView(APIView):
    """Session-based shopping cart. GET/POST/PATCH/DELETE operations on cart items."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = request.session.get('cart', {})
        return Response({'cart': cart})

    def post(self, request):
        product_id = str(request.data.get('product_id', ''))
        quantity = request.data.get('quantity', 1)

        if not product_id.isdigit():
            return Response({'detail': 'product_id must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.filter(id=product_id, is_active=True).first()
        if product is None:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            return Response({'detail': 'quantity must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        qty = max(1, qty)
        cart = request.session.get('cart', {})
        current = int(cart.get(product_id, 0))
        cart[product_id] = min(current + qty, product.stock)
        request.session['cart'] = cart
        return Response({'cart': cart}, status=status.HTTP_200_OK)

    def patch(self, request):
        product_id = str(request.data.get('product_id', ''))
        quantity = request.data.get('quantity')

        if not product_id.isdigit():
            return Response({'detail': 'product_id must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            return Response({'detail': 'quantity must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.filter(id=product_id, is_active=True).first()
        if product is None:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart = request.session.get('cart', {})
        if qty <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = min(qty, product.stock)
        request.session['cart'] = cart
        return Response({'cart': cart}, status=status.HTTP_200_OK)

    def delete(self, request):
        product_id = str(request.data.get('product_id', ''))
        cart = request.session.get('cart', {})
        if product_id:
            cart.pop(product_id, None)
        else:
            cart = {}
        request.session['cart'] = cart
        return Response({'cart': cart}, status=status.HTTP_200_OK)


class ProductReviewListCreateAPIView(APIView):
    """List/create reviews for a product. Enforces purchase verification on creation."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, product_id: int):
        product = Product.objects.filter(id=product_id, is_active=True).first()
        if product is None:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        reviews_qs = Review.objects.filter(product=product).select_related('user').order_by('-created_at')

        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(reviews_qs, request)
        serializer = ReviewSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, product_id: int):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        product = Product.objects.filter(id=product_id, is_active=True).first()
        if product is None:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        purchased = OrderItem.objects.filter(order__user=request.user, product=product).exists()
        if not purchased:
            return Response(
                {'detail': 'Only customers who purchased this product can leave a review.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if Review.objects.filter(product=product, user=request.user).exists():
            return Response({'detail': 'You have already reviewed this product.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
