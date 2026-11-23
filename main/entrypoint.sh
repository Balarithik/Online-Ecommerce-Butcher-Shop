#!/bin/sh
set -e

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

# Bootstrap an initial admin only when all credentials are explicitly supplied.
# Existing accounts are never modified, so container restarts are safe.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "==> Checking initial administrator..."
    python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
if User.objects.filter(username=username).exists():
    print("Initial administrator already exists; leaving it unchanged.")
else:
    User.objects.create_superuser(
        username=username,
        email=os.environ["DJANGO_SUPERUSER_EMAIL"],
        password=os.environ["DJANGO_SUPERUSER_PASSWORD"],
    )
    print("Initial administrator created.")
PY
else
    echo "==> Initial administrator bootstrap skipped (credentials not configured)."
fi

echo "==> Launching server..."
exec "$@"
