import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial Django superuser from DJANGO_SUPERUSER_* environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        missing = [
            name for name, value in (
                ("DJANGO_SUPERUSER_USERNAME", username),
                ("DJANGO_SUPERUSER_EMAIL", email),
                ("DJANGO_SUPERUSER_PASSWORD", password),
            )
            if not value
        ]
        if missing:
            self.stdout.write(self.style.WARNING(
                "Superuser bootstrap skipped. Set these Render environment variables: "
                + ", ".join(missing)
            ))
            return

        User = get_user_model()
        existing = User.objects.filter(**{User.USERNAME_FIELD: username}).first()

        if existing:
            if existing.is_superuser and existing.is_staff:
                self.stdout.write(self.style.SUCCESS(
                    f"Superuser '{username}' already exists; no changes made."
                ))
                return
            raise CommandError(
                f"Account '{username}' already exists but is not a superuser. "
                "For safety, bootstrap did not change its privileges. Choose a new "
                "DJANGO_SUPERUSER_USERNAME or promote the account manually."
            )

        User.objects.create_superuser(
            **{
                User.USERNAME_FIELD: username,
                "email": email,
                "password": password,
            }
        )
        self.stdout.write(self.style.SUCCESS(
            f"Initial superuser '{username}' created successfully."
        ))
