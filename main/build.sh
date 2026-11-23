#!/usr/bin/env bash
set -euo pipefail

# Build-time tasks only. Create migrations during development and commit them.
pip install -r requirements.txt
python manage.py collectstatic --noinput
