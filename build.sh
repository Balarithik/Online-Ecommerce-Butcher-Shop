#!/usr/bin/env bash

cd main 

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py makemigration

python manage.py migrate