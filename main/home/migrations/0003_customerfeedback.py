from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0002_customerprofile_number_of_orders"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("website", "Website experience"), ("products", "Products and pricing"), ("ordering", "Cart and checkout"), ("delivery", "Delivery experience"), ("other", "Other")], default="website", max_length=20)),
                ("rating", models.PositiveSmallIntegerField(choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")])),
                ("message", models.TextField(max_length=1500)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="submitted_feedback", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
