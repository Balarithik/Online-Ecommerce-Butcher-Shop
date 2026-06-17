#!/usr/bin/env bash


pip install -r requirements.txt

python main/manage.py collectstatic --noinput

python main/manage.py makemigrations

python main/manage.py migrate
