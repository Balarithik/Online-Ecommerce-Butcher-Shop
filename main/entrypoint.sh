#!/bin/sh
set -eu

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Creating initial superuser (if not already present)..."
python manage.py bootstrap_superuser

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting application..."
exec "$@"
