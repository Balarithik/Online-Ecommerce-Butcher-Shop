from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0015_notification_delivery")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="sms_opt_in",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="notificationdelivery",
            name="channel",
            field=models.CharField(
                choices=[("email", "Email"), ("whatsapp", "WhatsApp"), ("sms", "SMS")],
                max_length=12,
            ),
        ),
    ]
