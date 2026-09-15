from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0009_alter_order_status')]

    operations = [
        migrations.AlterField(model_name='order', name='order_id', field=models.AutoField(primary_key=True, serialize=False)),
        migrations.AlterField(
            model_name='order', name='quantity',
            field=models.DecimalField(decimal_places=3, default=Decimal('1.000'), max_digits=6,
                                      validators=[MinValueValidator(Decimal('0.250')), MaxValueValidator(Decimal('100.000'))]),
        ),
        migrations.AlterField(
            model_name='order', name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))]),
        ),
    ]
