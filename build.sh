#!/usr/bin/env bash


pip install -r requirements.txt

cd main 

python manage.py collectstatic --noinput

python manage.py makemigrations

python manage.py migrate
