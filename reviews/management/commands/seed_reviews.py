import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from products.models import Product
from reviews.models import Review

COMMENTS = [
    'Great quality!',
    'Works perfectly for brewing.',
    'Very fresh and aromatic.',
    'Excellent value for money.',
    'Would buy again.',
    'Reliable ingredient for my batches.',
    'Tasty result in the final beer.',
]


class Command(BaseCommand):
    help = 'Seed demo reviews for existing products'

    def _ensure_users(self) -> list:
        """Ensure at least two users exist for seeding reviews."""
        User = get_user_model()
        users = list(User.objects.all())

        if len(users) >= 2:
            return users

        demo_accounts = [
            ('demo_reviewer1', 'demo1@example.com'),
            ('demo_reviewer2', 'demo2@example.com'),
        ]

        for username, email in demo_accounts:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email},
            )
            if created:
                user.set_password('demo12345')
                user.save(update_fields=['password'])
                self.stdout.write(self.style.SUCCESS(f'Created demo user: {username}'))

        return list(User.objects.all())

    def handle(self, *args, **options):
        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.WARNING('No products found. Seed products first.'))
            return

        users = self._ensure_users()
        if not users:
            self.stdout.write(self.style.WARNING('No users available to create reviews.'))
            return

        created_count = 0
        examples = []

        for product in products:
            reviews_target = random.randint(1, 2)
            random.shuffle(users)

            existing_user_ids = set(
                Review.objects.filter(product=product).values_list('user_id', flat=True)
            )
            available_users = [user for user in users if user.id not in existing_user_ids]

            for user in available_users[:reviews_target]:
                review, created = Review.objects.get_or_create(
                    product=product,
                    user=user,
                    defaults={
                        'rating': random.randint(3, 5),
                        'comment': random.choice(COMMENTS),
                    },
                )
                if not created:
                    continue

                created_count += 1
                if len(examples) < 8:
                    examples.append(
                        f'- {product.name}: {user.username} rated {review.rating}/5 — {review.comment}'
                    )

        if created_count == 0:
            self.stdout.write(self.style.WARNING('No new reviews were created (all combinations exist).'))
            return

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} review(s).'))
        self.stdout.write('Example reviews created:')
        for line in examples:
            self.stdout.write(line)
