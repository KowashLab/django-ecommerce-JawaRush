import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Product

User = get_user_model()

DEMO_USERS = ['user1', 'user2']
STATUSES = ['pending', 'paid', 'shipped', 'delivered']
PAYMENT_METHODS = ['card', 'cash']
SHIPPING_ADDRESSES = [
    '123 Test Street, Springfield',
    '456 Brew Lane, Portland',
    '789 Hop Ave, Denver',
    '321 Malt Rd, Austin',
]
FULL_NAMES = {
    'user1': 'Alice Brewer',
    'user2': 'Bob Maltman',
}
PHONES = {
    'user1': '+1 (555) 010-0001',
    'user2': '+1 (555) 010-0002',
}

# Maximum orders per user — prevents explosion on repeated runs
MAX_ORDERS_PER_USER = 3


class Command(BaseCommand):
    help = 'Seed realistic demo orders for demo users (safe to re-run)'

    def handle(self, *args, **options):
        products = list(Product.objects.filter(is_active=True))
        if not products:
            self.stdout.write(self.style.ERROR('No active products found. Run seed_products first.'))
            return

        created_count = 0
        now = timezone.now()

        for username in DEMO_USERS:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User "{username}" not found, skipping.'))
                continue

            existing = Order.objects.filter(user=user).count()
            to_create = max(0, MAX_ORDERS_PER_USER - existing)

            if to_create == 0:
                self.stdout.write(f'  {username}: already has {existing} order(s), skipping.')
                continue

            for i in range(to_create):
                status = STATUSES[i % len(STATUSES)]
                selected = random.sample(products, k=min(random.randint(1, 3), len(products)))
                quantities = {p.id: random.randint(1, 3) for p in selected}
                total = sum(p.price * quantities[p.id] for p in selected)
                days_ago = random.randint(1, 14)

                order = Order.objects.create(
                    user=user,
                    status=status,
                    total_price=total,
                    shipping_address=random.choice(SHIPPING_ADDRESSES),
                    full_name=FULL_NAMES.get(username, username),
                    phone=PHONES.get(username, '+10000000000'),
                    payment_method=random.choice(PAYMENT_METHODS),
                )
                # Back-date created_at for realism
                Order.objects.filter(pk=order.pk).update(
                    created_at=now - timedelta(days=days_ago, hours=random.randint(0, 23))
                )

                for product in selected:
                    qty = quantities[product.id]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        price=product.price,
                    )

                created_count += 1
                self.stdout.write(
                    f'  Order #{order.pk} for {username}: {len(selected)} item(s), '
                    f'status={status}, total=${total:.2f}, {days_ago}d ago'
                )

        total_orders = Order.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nCreated {created_count} new order(s). Total orders in DB: {total_orders}'
        ))
