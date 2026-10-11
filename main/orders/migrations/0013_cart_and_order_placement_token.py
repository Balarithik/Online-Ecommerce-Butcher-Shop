import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


def gen_unique_placement_tokens(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.all():
        order.placement_token = uuid.uuid4()
        order.save(update_fields=['placement_token'])

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0012_order_latitude_order_longitude'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0005_product_price_and_availability'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='placement_token',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.RunPython(gen_unique_placement_tokens, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='placement_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, db_index=True, max_length=40, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=3, default=Decimal('1.000'), max_digits=6, validators=[MinValueValidator(Decimal('0.250'))])),
                ('cut_preference', models.CharField(default='Curry Cut (Medium)', max_length=100)),
                ('delivery_slot', models.CharField(default='Express Delivery (45-60 Mins)', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.cart')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.products')),
            ],
            options={
                'unique_together': {('cart', 'product')},
            },
        ),
        migrations.AddConstraint(
            model_name='cart',
            constraint=models.UniqueConstraint(
                condition=models.Q(user__isnull=True),
                fields=('session_key',),
                name='unique_guest_cart_session',
            ),
        ),
    ]
