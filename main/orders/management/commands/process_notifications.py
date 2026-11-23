from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from orders.models import NotificationDelivery
from orders.notifications import deliver_notification


class Command(BaseCommand):
    help = "Process pending Lakshmi Broliers customer notifications."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        # Recover claims left behind by a worker crash after 10 minutes.
        NotificationDelivery.objects.filter(
            status="processing", updated_at__lt=timezone.now() - timedelta(minutes=10)
        ).update(status="pending", next_attempt_at=timezone.now())
        limit = max(1, min(options["limit"], 500))
        processed = 0
        ids = list(NotificationDelivery.objects.filter(
            status="pending", next_attempt_at__lte=timezone.now()
        ).order_by("created_at").values_list("pk", flat=True)[:limit])
        for pk in ids:
            with transaction.atomic():
                delivery = NotificationDelivery.objects.select_for_update().filter(
                    pk=pk, status="pending", next_attempt_at__lte=timezone.now()
                ).first()
                if delivery is None:
                    continue
                delivery.status = "processing"
                delivery.save(update_fields=["status", "updated_at"])
            deliver_notification(delivery)
            processed += 1
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} notification(s)."))
