from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Order, OrderItem
from products.models import Category, Product

User = get_user_model()


class OrderModelTests(TestCase):
    """Test Order model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name='John Doe',
            phone='1234567890',
            shipping_address='123 Main St',
            status=Order.Status.PENDING,
            payment_method=Order.PaymentMethod.CARD,
            total_price=100.00,
        )

    def test_order_creation(self):
        """Test basic order creation."""
        self.assertEqual(self.order.full_name, 'John Doe')
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_order_string_representation(self):
        """Test __str__ method."""
        self.assertIn(str(self.order.pk), str(self.order))
        self.assertIn('testuser', str(self.order))

    def test_order_user_relationship(self):
        """Test user foreign key."""
        self.assertEqual(self.order.user, self.user)

    def test_order_status_choices(self):
        """Test order status options."""
        self.assertIn(Order.Status.PENDING, Order.Status.values)
        self.assertIn(Order.Status.PAID, Order.Status.values)
        self.assertIn(Order.Status.SHIPPED, Order.Status.values)
        self.assertIn(Order.Status.DELIVERED, Order.Status.values)

    def test_order_payment_method_choices(self):
        """Test payment method options."""
        self.assertIn(Order.PaymentMethod.CARD, Order.PaymentMethod.values)
        self.assertIn(Order.PaymentMethod.CASH, Order.PaymentMethod.values)

    def test_order_anonymous_user(self):
        """Test order without user (anonymous)."""
        anon_order = Order.objects.create(
            full_name='Anonymous',
            phone='0000000000',
            shipping_address='Unknown',
            total_price=50.00,
        )
        self.assertIsNone(anon_order.user)

    def test_order_ordering(self):
        """Test orders are ordered by created_at descending."""
        order2 = Order.objects.create(
            user=self.user,
            full_name='Jane',
            phone='9999999999',
            shipping_address='456 Oak Ave',
            total_price=200.00,
        )
        orders = Order.objects.all()
        self.assertEqual(orders[0], order2)  # Newest first


class OrderItemModelTests(TestCase):
    """Test OrderItem model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.category = Category.objects.create(
            name='Category',
            slug='category',
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Description',
            price=Decimal('50.00'),
            category=self.category,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name='Test',
            total_price=Decimal('150.00'),
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            price=Decimal('50.00'),
        )

    def test_order_item_creation(self):
        """Test basic order item creation."""
        self.assertEqual(self.order_item.quantity, 3)
        self.assertEqual(self.order_item.price, Decimal('50.00'))

    def test_order_item_string_representation(self):
        """Test __str__ method."""
        self.assertIn('Test Product', str(self.order_item))
        self.assertIn('x3', str(self.order_item))

    def test_order_item_order_relationship(self):
        """Test order foreign key."""
        self.assertEqual(self.order_item.order, self.order)

    def test_order_item_product_relationship(self):
        """Test product foreign key."""
        self.assertEqual(self.order_item.product, self.product)

    def test_multiple_items_per_order(self):
        """Test multiple order items in one order."""
        product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Description 2',
            price=Decimal('30.00'),
            category=self.category,
        )
        item2 = OrderItem.objects.create(
            order=self.order,
            product=product2,
            quantity=2,
            price=Decimal('30.00'),
        )
        items = self.order.items.all()
        self.assertEqual(items.count(), 2)
        self.assertIn(self.order_item, items)
        self.assertIn(item2, items)


class CartViewTests(TestCase):
    """Test cart operations."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Test Cat',
            slug='test-cat',
        )
        self.product = Product.objects.create(
            name='Cart Product',
            slug='cart-product',
            description='Test',
            price=Decimal('10.00'),
            category=self.category,
            stock=100,
        )

    def test_cart_detail_view_loads(self):
        """Test cart page loads."""
        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.status_code, 200)

    def test_cart_detail_empty(self):
        """Test empty cart displays correctly."""
        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.context['cart_total'], Decimal('0'))

    def test_add_to_cart(self):
        """Test adding product to cart."""
        response = self.client.post(
            reverse('add_to_cart', kwargs={'product_id': self.product.id}),
            follow=True,
        )
        session = self.client.session
        self.assertIn(str(self.product.id), session.get('cart', {}))

    def test_add_to_cart_multiple(self):
        """Test adding same product multiple times."""
        self.client.post(
            reverse('add_to_cart', kwargs={'product_id': self.product.id}),
        )
        self.client.post(
            reverse('add_to_cart', kwargs={'product_id': self.product.id}),
        )
        session = self.client.session
        cart = session.get('cart', {})
        self.assertEqual(cart.get(str(self.product.id)), 2)

    def test_add_to_cart_exceeds_stock(self):
        """Test quantity capped at stock level."""
        product = Product.objects.create(
            name='Limited Stock',
            slug='limited',
            description='Test',
            price=Decimal('5.00'),
            category=self.category,
            stock=3,
        )
        # Try to add more than stock
        for _ in range(5):
            self.client.post(
                reverse('add_to_cart', kwargs={'product_id': product.id}),
            )
        session = self.client.session
        cart = session.get('cart', {})
        # Should be capped at stock
        self.assertEqual(cart.get(str(product.id)), 3)

    def test_remove_from_cart(self):
        """Test removing product from cart."""
        self.client.post(
            reverse('add_to_cart', kwargs={'product_id': self.product.id}),
        )
        self.client.post(
            reverse('remove_from_cart', kwargs={'product_id': self.product.id}),
        )
        session = self.client.session
        cart = session.get('cart', {})
        self.assertNotIn(str(self.product.id), cart)

    def test_update_cart_quantity(self):
        """Test updating product quantity."""
        self.client.post(
            reverse('add_to_cart', kwargs={'product_id': self.product.id}),
        )
        self.client.post(
            reverse('update_cart', kwargs={'product_id': self.product.id}),
            {'quantity': 5},
        )
        session = self.client.session
        cart = session.get('cart', {})
        self.assertEqual(cart.get(str(self.product.id)), 5)

    def test_update_cart_invalid_quantity(self):
        """Test invalid quantity defaults to 1."""
        self.client.post(
            reverse('add_to_cart', kwargs={'product_id': self.product.id}),
        )
        self.client.post(
            reverse('update_cart', kwargs={'product_id': self.product.id}),
            {'quantity': 'invalid'},
        )
        session = self.client.session
        cart = session.get('cart', {})
        self.assertEqual(cart.get(str(self.product.id)), 1)


class CheckoutViewTests(TestCase):
    """Test checkout view."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Cat',
            slug='cat',
        )
        self.product = Product.objects.create(
            name='Checkout Product',
            slug='checkout-product',
            description='Test',
            price=Decimal('20.00'),
            category=self.category,
            stock=50,
        )

    def test_checkout_view_loads(self):
        """Test checkout page GET with empty cart."""
        response = self.client.get(reverse('checkout'))
        # May redirect if cart is empty, or show form
        self.assertIn(response.status_code, [200, 302])

    def test_checkout_empty_cart_redirect(self):
        """Test empty cart redirects."""
        response = self.client.post(reverse('checkout'))
        self.assertRedirects(response, reverse('cart_detail'))

    def test_checkout_creates_order(self):
        """Test checkout creates order and items."""
        # Add to cart
        session = self.client.session
        session['cart'] = {str(self.product.id): 2}
        session.save()

        # Checkout
        response = self.client.post(
            reverse('checkout'),
            {
                'full_name': 'Test User',
                'phone': '1234567890',
                'shipping_address': '123 Main St',
                'payment_method': 'card',
            },
        )

        # Verify order created
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.full_name, 'Test User')
        self.assertEqual(order.total_price, Decimal('40.00'))

    def test_checkout_creates_order_items(self):
        """Test checkout creates order items."""
        session = self.client.session
        session['cart'] = {str(self.product.id): 3}
        session.save()

        self.client.post(
            reverse('checkout'),
            {
                'full_name': 'Test',
                'phone': '9999999999',
                'shipping_address': 'Address',
                'payment_method': 'cash',
            },
        )

        order_items = OrderItem.objects.all()
        self.assertEqual(order_items.count(), 1)
        self.assertEqual(order_items[0].quantity, 3)

    def test_checkout_reduces_stock(self):
        """Test checkout reduces product stock."""
        original_stock = self.product.stock
        session = self.client.session
        session['cart'] = {str(self.product.id): 5}
        session.save()

        self.client.post(
            reverse('checkout'),
            {
                'full_name': 'Test',
                'phone': '9999999999',
                'shipping_address': 'Address',
                'payment_method': 'card',
            },
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, original_stock - 5)

    def test_checkout_authenticated_user(self):
        """Test checkout with authenticated user."""
        user = User.objects.create_user(
            username='auth_user',
            password='secure123',
        )
        self.client.login(username='auth_user', password='secure123')

        session = self.client.session
        session['cart'] = {str(self.product.id): 1}
        session.save()

        self.client.post(
            reverse('checkout'),
            {
                'full_name': 'Auth User',
                'phone': '5555555555',
                'shipping_address': 'User Address',
                'payment_method': 'card',
            },
        )

        order = Order.objects.first()
        self.assertEqual(order.user, user)
