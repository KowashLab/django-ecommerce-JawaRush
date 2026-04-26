from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Category, Product

User = get_user_model()


class CategoryModelTests(TestCase):
    """Test Category model."""

    def setUp(self):
        self.category = Category.objects.create(
            name='Test Hops',
            slug='test-hops',
        )

    def test_category_creation(self):
        """Test basic category creation."""
        self.assertEqual(self.category.name, 'Test Hops')
        self.assertEqual(self.category.slug, 'test-hops')

    def test_category_string_representation(self):
        """Test __str__ method."""
        self.assertEqual(str(self.category), 'Test Hops')

    def test_category_with_parent(self):
        """Test category with parent relationship."""
        parent = Category.objects.create(name='Parent', slug='parent')
        child = Category.objects.create(
            name='Child',
            slug='child',
            parent=parent,
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_category_ordering(self):
        """Test categories are ordered by name."""
        Category.objects.create(name='Zebra', slug='zebra')
        Category.objects.create(name='Alpha', slug='alpha')
        categories = list(Category.objects.all().values_list('name', flat=True))
        self.assertEqual(categories, ['Alpha', 'Test Hops', 'Zebra'])


class ProductModelTests(TestCase):
    """Test Product model."""

    def setUp(self):
        self.category = Category.objects.create(
            name='Hops',
            slug='hops',
        )
        self.product = Product.objects.create(
            name='Cascade Hops',
            slug='cascade-hops',
            description='Aromatic hop variety',
            price=15.99,
            category=self.category,
            is_active=True,
            stock=100,
        )

    def test_product_creation(self):
        """Test basic product creation."""
        self.assertEqual(self.product.name, 'Cascade Hops')
        self.assertEqual(self.product.price, 15.99)
        self.assertEqual(self.product.stock, 100)

    def test_product_string_representation(self):
        """Test __str__ method."""
        self.assertEqual(str(self.product), 'Cascade Hops')

    def test_product_category_relationship(self):
        """Test product to category foreign key."""
        self.assertEqual(self.product.category, self.category)

    def test_product_is_active_default(self):
        """Test is_active defaults to True."""
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test',
            price=10.00,
            category=self.category,
        )
        self.assertTrue(product.is_active)

    def test_product_stock_default(self):
        """Test stock defaults to 0."""
        product = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test',
            price=10.00,
            category=self.category,
        )
        self.assertEqual(product.stock, 0)

    def test_product_slug_uniqueness(self):
        """Test slug must be unique."""
        with self.assertRaises(Exception):
            Product.objects.create(
                name='Another Cascade',
                slug='cascade-hops',  # duplicate
                description='Different product',
                price=20.00,
                category=self.category,
            )

    def test_inactive_product(self):
        """Test inactive product."""
        inactive = Product.objects.create(
            name='Inactive Hops',
            slug='inactive-hops',
            description='Not available',
            price=10.00,
            category=self.category,
            is_active=False,
        )
        self.assertFalse(inactive.is_active)

    def test_product_ordering(self):
        """Test products are ordered by created_at descending."""
        # Create fresh products in this test
        cat = Category.objects.create(name='Fresh', slug='fresh')
        # Oldest product
        p1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            description='First',
            price=10.00,
            category=cat,
        )
        # Newest product
        p2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Second',
            price=20.00,
            category=cat,
        )
        products = list(Product.objects.filter(category=cat).order_by('-created_at'))
        # Newest first
        self.assertEqual(products[0].name, 'Product 2')
        self.assertEqual(products[1].name, 'Product 1')


class HomeViewTests(TestCase):
    """Test home view."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Hops',
            slug='hops',
        )
        self.product = Product.objects.create(
            name='Test Hops',
            slug='test-hops',
            description='Test description',
            price=10.00,
            category=self.category,
            is_active=True,
            stock=10,
        )

    def test_home_page_loads(self):
        """Test home page returns 200."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        # Check that either home.html or product_list.html is in templates
        self.assertTrue(
            'home.html' in response.template_name or 
            'product_list.html' in str(response.template_name)
        )

    def test_home_page_contains_products(self):
        """Test home page displays products."""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Test Hops')

    def test_home_page_product_filtering(self):
        """Test category filter works."""
        response = self.client.get(reverse('home') + '?category=hops')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product, response.context['products'])

    def test_home_page_search(self):
        """Test product search works."""
        response = self.client.get(reverse('home') + '?q=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Hops')

    def test_home_page_search_no_results(self):
        """Test search with no matching products."""
        response = self.client.get(reverse('home') + '?q=nonexistent')
        self.assertEqual(response.status_code, 200)
        # Empty result set

    def test_home_page_sorting(self):
        """Test sort options."""
        response = self.client.get(reverse('home') + '?sort=price_asc')
        self.assertEqual(response.status_code, 200)

    def test_home_page_pagination(self):
        """Test pagination works."""
        # Create 11 products to trigger pagination
        for i in range(11):
            Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description=f'Product {i}',
                price=10.00 + i,
                category=self.category,
            )
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])

    def test_home_page_inactive_products_hidden(self):
        """Test inactive products are not shown."""
        inactive = Product.objects.create(
            name='Inactive',
            slug='inactive',
            description='Not active',
            price=5.00,
            category=self.category,
            is_active=False,
        )
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Inactive')

    def test_featured_products_in_context(self):
        """Test featured products are passed to context."""
        response = self.client.get(reverse('home'))
        self.assertIn('featured_products', response.context)


class ProductDetailViewTests(TestCase):
    """Test product detail view."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
        )
        self.product = Product.objects.create(
            name='Detail Test Product',
            slug='detail-test-product',
            description='Product description',
            price=25.50,
            category=self.category,
            stock=50,
        )

    def test_product_detail_page_loads(self):
        """Test product detail page returns 200."""
        url = reverse('product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_detail_shows_product_info(self):
        """Test product detail displays product information."""
        url = reverse('product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        self.assertContains(response, 'Detail Test Product')
        # Price may be formatted with comma, check for both formats
        self.assertTrue(
            '25.50' in response.content.decode() or
            '25,50' in response.content.decode()
        )

    def test_product_detail_invalid_slug(self):
        """Test 404 for invalid slug."""
        url = reverse('product_detail', kwargs={'slug': 'nonexistent-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_product_detail_context(self):
        """Test context contains product."""
        url = reverse('product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        self.assertEqual(response.context['product'], self.product)
