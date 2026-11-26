import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import NotificationDelivery
from orders.notifications import deliver_notification


class Command(BaseCommand):
    help = "Process pending Lakshmi Broilers customer notifications."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Keep polling for pending notifications (for a Render background worker).",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=30,
            help="Seconds between polling cycles when --loop is enabled (minimum 5).",
        )

    def _process_batch(self, limit):
        # Recover claims left behind by a worker crash after 10 minutes.
        now = timezone.now()
        NotificationDelivery.objects.filter(
            status="processing",
            updated_at__lt=now - timedelta(minutes=10),
        ).update(status="pending", next_attempt_at=now)

        processed = 0
        ids = list(
            NotificationDelivery.objects.filter(
                status="pending",
                next_attempt_at__lte=now,
            )
            .order_by("created_at")
            .values_list("pk", flat=True)[:limit]
        )
        for pk in ids:
            with transaction.atomic():
                delivery = (
                    NotificationDelivery.objects.select_for_update()
                    .filter(
                        pk=pk,
                        status="pending",
                        next_attempt_at__lte=timezone.now(),
                    )
                    .first()
                )
                if delivery is None:
                    continue
                delivery.status = "processing"
                delivery.save(update_fields=["status", "updated_at"])

            deliver_notification(delivery)
            processed += 1

        return processed

    def handle(self, *args, **options):
        limit = max(1, min(options["limit"], 500))
        interval = max(5, min(options["interval"], 300))

        if not options["loop"]:
            processed = self._process_batch(limit)
            self.stdout.write(self.style.SUCCESS(f"Processed {processed} notification(s)."))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Notification worker started (poll interval: {interval}s, batch limit: {limit})."
        ))
        try:
            while True:
                processed = self._process_batch(limit)
                if processed:
                    self.stdout.write(f"Processed {processed} notification(s).")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Notification worker stopped."))
