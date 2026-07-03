#!/usr/bin/env bash

pip install --upgrade pip

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py makemigrations

python manage.py migrate

python manage.py auto_createsuperuser --username admin --password admin123
