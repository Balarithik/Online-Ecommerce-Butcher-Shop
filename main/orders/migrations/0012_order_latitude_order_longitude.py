from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_order_created_at_order_cut_preference_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='latitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[
                    MinValueValidator(Decimal('-90')),
                    MaxValueValidator(Decimal('90')),
                ],
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='longitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[
                    MinValueValidator(Decimal('-180')),
                    MaxValueValidator(Decimal('180')),
                ],
            ),
        ),
    ]
