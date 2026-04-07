from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0001_initial'),
    ]

    operations = [
        # Fix PENDING typo: 'penging' → 'pending'
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Ожидает'), ('paid', 'Оплачен'), ('shipped', 'Отправлен'), ('delivered', 'Доставлен'), ('cancelled', 'Отменен')],
                default='pending',
                max_length=20,
                verbose_name='Статус',
            ),
        ),
        # Allow anonymous orders (user=NULL)
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Пользователь',
            ),
        ),
        # Fix shipping_address: allow blank
        migrations.AlterField(
            model_name='order',
            name='shipping_address',
            field=models.TextField(blank=True, default='', verbose_name='Адрес доставки'),
        ),
        # Fix full_name: allow blank + fix typo
        migrations.AlterField(
            model_name='order',
            name='full_name',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Получатель'),
        ),
        # Add phone field (was missing due to trailing comma bug)
        migrations.AddField(
            model_name='order',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Телефон'),
        ),
    ]
