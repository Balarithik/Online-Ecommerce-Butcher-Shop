from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [("orders", "0006_order_instructions_order_product_id_alter_order_id_and_more")]
    operations = [
        migrations.AddField(model_name="order", name="whatsapp_opt_in",
                            field=models.BooleanField(default=False)),
        migrations.CreateModel(
            name="NotificationDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel", models.CharField(choices=[("email", "Email"), ("whatsapp", "WhatsApp")], max_length=12)),
                ("event", models.CharField(choices=[("order_placed", "Order placed"), ("pending", "Order confirmed"), ("preparing", "Preparing"), ("out_for_delivery", "Out for delivery"), ("delivered", "Delivered"), ("cancelled", "Cancelled")], max_length=24)),
                ("recipient", models.CharField(max_length=254)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("sent", "Sent"), ("failed", "Failed")], default="pending", max_length=12)),
                ("attempt_count", models.PositiveSmallIntegerField(default=0)),
                ("provider_message_id", models.CharField(blank=True, max_length=255)),
                ("last_error", models.TextField(blank=True)),
                ("next_attempt_at", models.DateTimeField(default=timezone.now, null=True, blank=True)),
                ("sent_at", models.DateTimeField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_deliveries", to="orders.order")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(model_name="notificationdelivery",
            constraint=models.UniqueConstraint(fields=("order", "channel", "event"),
                                               name="unique_order_notification_event")),
    ]
