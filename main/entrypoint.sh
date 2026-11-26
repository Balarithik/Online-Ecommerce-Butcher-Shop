#!/bin/sh
set -eu

if [ "${SKIP_DJANGO_STARTUP_TASKS:-0}" != "1" ]; then
    echo "==> Applying database migrations..."
    python manage.py migrate --noinput

    echo "==> Creating initial superuser (if not already present)..."
    python manage.py bootstrap_superuser

    echo "==> Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "==> Skipping web-service startup tasks for background worker..."
fi

echo "==> Starting application process..."
exec "$@"
