#!/bin/sh
set -e

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Checking initial administrator..."
python manage.py bootstrap_superuser

echo "==> Launching server..."
exec "$@"
