from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

# Create your models here.

class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        PAID = 'paid', 'Оплачен'
        SHIPPED = 'shipped', 'Отправлен'
        DELIVERED = 'delivered', 'Доставлен'
        CANCELLED = 'cancelled', 'Отменен'

    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Карта'
        CASH = 'cash', 'Наличные'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Пользователь',
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Итоговая сумма'
    )
    shipping_address = models.TextField(verbose_name='Адрес доставки', blank=True, default='')
    full_name = models.CharField(max_length=200, verbose_name='Получатель', blank=True, default='')
    phone = models.CharField(max_length=20, verbose_name='Телефон', blank=True, default='')
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD,
        verbose_name='Способ оплаты',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name='Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f'{self.pk} - {self.user.username}'
        return f'{self.pk} - Anonymous'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(verbose_name='Кол-во')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена на момент заказа'
    )
    class Meta:
        verbose_name='Позиция заказа'
        verbose_name_plural = 'Позиции заказа'


    def __str__(self):
        return f'{self.product.name} - x{self.quantity} '

