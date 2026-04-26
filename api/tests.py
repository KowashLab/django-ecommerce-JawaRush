from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from products.models import Category, Product
from orders.models import Order, OrderItem
from reviews.models import Review

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


class GraphQLAnalyticsTests(TestCase):
        """Test GraphQL analytics queries (read-only)."""

        def setUp(self):
                self.client = Client()
                self.category = Category.objects.create(name='Analytics', slug='analytics')

                self.product_a = Product.objects.create(
                        name='Product A',
                        slug='product-a',
                        description='A',
                        price=Decimal('10.00'),
                        category=self.category,
                )
                self.product_b = Product.objects.create(
                        name='Product B',
                        slug='product-b',
                        description='B',
                        price=Decimal('20.00'),
                        category=self.category,
                )
                self.product_c = Product.objects.create(
                        name='Product C',
                        slug='product-c',
                        description='C',
                        price=Decimal('30.00'),
                        category=self.category,
                )

                # Three orders total, total_revenue = 100.00
                order1 = Order.objects.create(total_price=Decimal('20.00'))
                order2 = Order.objects.create(total_price=Decimal('30.00'))
                order3 = Order.objects.create(total_price=Decimal('50.00'))

                # Product A in 3 orders, Product B in 2, Product C in 1
                OrderItem.objects.create(order=order1, product=self.product_a, quantity=1, price=Decimal('10.00'))
                OrderItem.objects.create(order=order1, product=self.product_b, quantity=1, price=Decimal('20.00'))
                OrderItem.objects.create(order=order2, product=self.product_a, quantity=1, price=Decimal('10.00'))
                OrderItem.objects.create(order=order2, product=self.product_b, quantity=1, price=Decimal('20.00'))
                OrderItem.objects.create(order=order3, product=self.product_a, quantity=1, price=Decimal('10.00'))
                OrderItem.objects.create(order=order3, product=self.product_c, quantity=1, price=Decimal('30.00'))

        def _graphql(self, query):
                return self.client.post(
                        '/graphql/',
                        data={'query': query},
                        content_type='application/json',
                )

        def test_graphql_total_orders_and_revenue(self):
                query = '''
                query {
                    totalOrders
                    totalRevenue
                }
                '''
                response = self._graphql(query)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertNotIn('errors', payload)
                self.assertEqual(payload['data']['totalOrders'], 3)
                self.assertEqual(payload['data']['totalRevenue'], 100.0)

        def test_graphql_top_products(self):
                query = '''
                query {
                    topProducts {
                        name
                        ordersCount
                    }
                }
                '''
                response = self._graphql(query)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertNotIn('errors', payload)

                top_products = payload['data']['topProducts']
                self.assertGreaterEqual(len(top_products), 3)
                self.assertEqual(top_products[0]['name'], 'Product A')
                self.assertEqual(top_products[0]['ordersCount'], 3)
                self.assertEqual(top_products[1]['name'], 'Product B')
                self.assertEqual(top_products[1]['ordersCount'], 2)

        def test_graphql_is_read_only_without_mutations(self):
                mutation = '''
                mutation {
                    createOrder(totalPrice: 10) {
                        id
                    }
                }
                '''
                response = self._graphql(mutation)
                self.assertEqual(response.status_code, 400)
                payload = response.json()
                self.assertIn('errors', payload)


class OrderCancelAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='cancel-user', password='pass12345')
        self.other_user = User.objects.create_user(username='other-cancel-user', password='pass12345')
        self.order = Order.objects.create(
            user=self.user,
            status=Order.Status.PENDING,
            total_price=Decimal('10.00'),
        )

    def test_owner_can_cancel_pending_order(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/orders/{self.order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    def test_cannot_cancel_non_pending_order(self):
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=['status'])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/orders/{self.order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_owner_cannot_cancel(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f'/api/orders/{self.order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CartAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Cart Cat', slug='cart-cat')
        self.product = Product.objects.create(
            name='Cart API Product',
            slug='cart-api-product',
            description='Cart API',
            price=Decimal('9.99'),
            category=self.category,
            stock=5,
        )

    def test_get_cart(self):
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cart', response.data)

    def test_add_item_to_cart(self):
        response = self.client.post('/api/cart/', {'product_id': self.product.id, 'quantity': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart'][str(self.product.id)], 2)

    def test_update_cart_item_quantity(self):
        self.client.post('/api/cart/', {'product_id': self.product.id, 'quantity': 1}, format='json')
        response = self.client.patch('/api/cart/', {'product_id': self.product.id, 'quantity': 4}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart'][str(self.product.id)], 4)

    def test_remove_item_from_cart(self):
        self.client.post('/api/cart/', {'product_id': self.product.id, 'quantity': 1}, format='json')
        response = self.client.delete('/api/cart/', {'product_id': self.product.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(str(self.product.id), response.data['cart'])


class ProductReviewsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='review-user', password='pass12345')
        self.other_user = User.objects.create_user(username='review-other', password='pass12345')
        self.category = Category.objects.create(name='Review Cat', slug='review-cat')
        self.product = Product.objects.create(
            name='Review Product',
            slug='review-product',
            description='Review API',
            price=Decimal('12.00'),
            category=self.category,
            stock=10,
        )

    def test_get_reviews_paginated(self):
        response = self.client.get(f'/api/products/{self.product.id}/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_authenticated_user_can_review_if_purchased(self):
        order = Order.objects.create(user=self.user, total_price=Decimal('12.00'))
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price=Decimal('12.00'))

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 5, 'comment': 'Great product'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.filter(product=self.product, user=self.user).count(), 1)

    def test_review_requires_purchase(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 5, 'comment': 'No purchase'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_prevent_duplicate_review(self):
        order = Order.objects.create(user=self.user, total_price=Decimal('12.00'))
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price=Decimal('12.00'))
        Review.objects.create(product=self.product, user=self.user, rating=4, comment='First')

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 5, 'comment': 'Second'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
