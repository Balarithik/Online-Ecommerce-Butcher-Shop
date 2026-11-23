#!/bin/sh
set -e

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Creating SuperUser ..."
python manage.py createsuperuser --noinput


echo "==> Launching server..."
exec "$@"
