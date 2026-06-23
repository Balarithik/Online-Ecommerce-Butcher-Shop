#!/usr/bin/env bash


pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py makemigrations

python manage.py migrate

echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'balarithik15@gmal.com', 'admin123')" | python manage.py shell