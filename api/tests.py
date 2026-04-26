from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from products.models import Category, Product
from orders.models import Order, OrderItem

User = get_user_model()


class ProductAPITests(TestCase):
    """Test Product API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name='Hops',
            slug='hops',
        )
        self.product = Product.objects.create(
            name='Cascade',
            slug='cascade',
            description='Hop variety',
            price=Decimal('15.00'),
            category=self.category,
            stock=100,
        )

    def test_product_list_unauthenticated(self):
        """Test product list accessible without auth."""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_product_retrieve(self):
        """Test product detail endpoint."""
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Cascade')

    def test_product_list_pagination(self):
        """Test product pagination."""
        for i in range(10):
            Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description='Test',
                price=Decimal('10.00'),
                category=self.category,
            )
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('next', response.data)

    def test_product_filter_by_category(self):
        """Test filter products by category."""
        response = self.client.get(f'/api/products/?category={self.category.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_product_filter_by_category_id(self):
        """Test filter products by category ID."""
        response = self.client.get(f'/api/products/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_product_create_forbidden(self):
        """Test products cannot be created via API (read-only)."""
        response = self.client.post(
            '/api/products/',
            {
                'name': 'New Hops',
                'slug': 'new-hops',
                'description': 'Test',
                'price': '20.00',
                'category': self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_product_update_forbidden(self):
        """Test products cannot be updated via API (read-only)."""
        response = self.client.patch(
            f'/api/products/{self.product.id}/',
            {'name': 'Updated'},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CategoryAPITests(TestCase):
    """Test Category API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name='Hop Types',
            slug='hop-types',
        )

    def test_category_list(self):
        """Test category list endpoint."""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_category_retrieve(self):
        """Test category detail endpoint."""
        response = self.client.get(f'/api/categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Hop Types')

    def test_category_create_forbidden(self):
        """Test categories cannot be created via API (read-only)."""
        response = self.client.post(
            '/api/categories/',
            {'name': 'New Category', 'slug': 'new-cat'},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class OrderAPITests(TestCase):
    """Test Order API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            password='apipass123',
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name='User 1',
            phone='1111111111',
            total_price=Decimal('100.00'),
        )
        self.other_order = Order.objects.create(
            user=self.other_user,
            full_name='User 2',
            phone='2222222222',
            total_price=Decimal('50.00'),
        )

    def test_order_list_unauthenticated(self):
        """Test unauthenticated user cannot access orders."""
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_list_authenticated(self):
        """Test authenticated user sees their orders."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'User 1')

    def test_order_user_sees_only_own_orders(self):
        """Test user only sees their own orders."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/orders/')
        self.assertEqual(len(response.data['results']), 1)
        # Should not see other user's order
        self.assertNotEqual(response.data['results'][0]['id'], self.other_order.id)

    def test_order_retrieve_own(self):
        """Test user can retrieve their own order."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/orders/{self.order.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'User 1')

    def test_order_retrieve_other_forbidden(self):
        """Test user cannot retrieve other user's order."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/orders/{self.other_order.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class JWTAuthTests(TestCase):
    """Test JWT authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='jwtuser',
            password='jwtpass123',
        )

    def test_obtain_token(self):
        """Test obtaining JWT tokens."""
        response = self.client.post(
            '/api/token/',
            {'username': 'jwtuser', 'password': 'jwtpass123'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_obtain_token_invalid_credentials(self):
        """Test obtaining token with wrong credentials."""
        response = self.client.post(
            '/api/token/',
            {'username': 'jwtuser', 'password': 'wrongpass'},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_with_jwt(self):
        """Test accessing protected endpoint with JWT token."""
        # Get token
        token_response = self.client.post(
            '/api/token/',
            {'username': 'jwtuser', 'password': 'jwtpass123'},
        )
        token = token_response.data['access']

        # Use token to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_token(self):
        """Test refreshing JWT token."""
        # Get token
        token_response = self.client.post(
            '/api/token/',
            {'username': 'jwtuser', 'password': 'jwtpass123'},
        )
        refresh = token_response.data['refresh']

        # Refresh token
        refresh_response = self.client.post(
            '/api/token/refresh/',
            {'refresh': refresh},
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_expired_token_rejected(self):
        """Test expired JWT token is rejected."""
        # This would require manipulating token expiry in real scenario
        # For now, test with invalid token format
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_auth_still_works(self):
        """Test session authentication still works alongside JWT."""
        self.client.login(username='jwtuser', password='jwtpass123')
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OrderItemNestedSerializerTests(TestCase):
    """Test order item nesting in order responses."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='nesteduser',
            password='nestedpass',
        )
        self.category = Category.objects.create(
            name='Test',
            slug='test',
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test',
            price=Decimal('25.00'),
            category=self.category,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name='Nested Test',
            total_price=Decimal('75.00'),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            price=Decimal('25.00'),
        )

    def test_order_includes_items(self):
        """Test order response includes nested items."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/orders/{self.order.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['quantity'], 3)

    def test_order_item_product_nested(self):
        """Test order item includes product name."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/orders/{self.order.id}/')
        item = response.data['items'][0]
        # Check that product info is in the item
        self.assertIn('product_name', item)
        self.assertEqual(item['product_name'], 'Test Product')
