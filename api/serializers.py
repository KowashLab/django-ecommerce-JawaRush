from decimal import Decimal

from rest_framework import serializers

from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent')


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'price',
            'stock',
            'is_active',
            'image',
            'category',
            'category_id',
            'created_at',
            'updated_at',
        )


class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'price')


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product = ProductSummarySerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source='product',
        queryset=Product.objects.filter(is_active=True),
        write_only=True,
        required=True,
    )

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_id', 'product_name', 'quantity', 'price')
        extra_kwargs = {
            'price': {'required': False},
        }


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'status',
            'total_price',
            'shipping_address',
            'full_name',
            'phone',
            'payment_method',
            'created_at',
            'updated_at',
            'items',
        )
        read_only_fields = ('user', 'total_price', 'created_at', 'updated_at')

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # If items were not provided explicitly, fallback to session cart.
        if not items_data:
            request = self.context.get('request')
            cart = request.session.get('cart', {}) if request else {}
            for product_id, quantity in cart.items():
                product = Product.objects.filter(id=product_id, is_active=True).first()
                if product is None:
                    continue
                try:
                    qty = int(quantity)
                except (TypeError, ValueError):
                    continue
                qty = max(1, min(qty, product.stock))
                if qty < 1:
                    continue
                items_data.append({'product': product, 'quantity': qty, 'price': product.price})

        if not items_data:
            raise serializers.ValidationError('Order must contain at least one item.')

        order = Order.objects.create(**validated_data)

        total = Decimal('0')
        order_items = []
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            quantity = min(quantity, product.stock)
            if quantity < 1:
                continue
            price = item_data.get('price', product.price)
            total += price * quantity
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price,
                )
            )

        if not order_items:
            order.delete()
            raise serializers.ValidationError('Order must contain at least one in-stock item.')

        OrderItem.objects.bulk_create(order_items)

        for item in order_items:
            item.product.stock -= item.quantity
            item.product.save(update_fields=['stock'])

        order.total_price = total
        order.save(update_fields=['total_price'])

        request = self.context.get('request')
        if request:
            request.session['cart'] = {}

        return order


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
