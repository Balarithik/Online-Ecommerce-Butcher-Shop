from decimal import Decimal
from django.db import migrations, models
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0005_product_price_and_availability'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('common_price_per_kg', models.DecimalField(
                    decimal_places=2, default=Decimal('0.00'), max_digits=10,
                    validators=[MinValueValidator(Decimal('0.01'))],
                    help_text='When saved, this rate is applied to every product currently in the catalog.',
                )),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
