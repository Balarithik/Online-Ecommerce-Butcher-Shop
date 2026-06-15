#!/usr/bin/env bash


pip install -r requirements.txt

cd main 

python manage.py collectstatic --noinput

python manage.py makemigration

python manage.py migrate
