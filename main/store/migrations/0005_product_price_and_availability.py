from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('store', '0004_alter_products_image1_alter_products_image2_and_more')]

    operations = [
        migrations.AlterField(
            model_name='products', name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='products', name='is_available',
            field=models.BooleanField(default=True),
        ),
    ]
