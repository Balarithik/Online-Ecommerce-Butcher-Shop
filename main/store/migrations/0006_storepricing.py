from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0005_product_price_and_availability"),
    ]

    operations = [
        migrations.CreateModel(
            name="StorePricing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("common_price", models.DecimalField(
                    decimal_places=2,
                    default=Decimal("240.00"),
                    max_digits=10,
                    validators=[MinValueValidator(Decimal("0.01"))],
                )),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Store pricing",
                "verbose_name_plural": "Store pricing",
            },
        ),
        migrations.RunPython(
            lambda apps, schema_editor: apps.get_model("store", "StorePricing").objects.get_or_create(
                pk=1, defaults={"common_price": Decimal("240.00")}
            ),
            migrations.RunPython.noop,
        ),
    ]
