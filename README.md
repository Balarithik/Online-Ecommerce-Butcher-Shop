# AramCuts V1

A Django-template ordering site for one local poultry shop. Customers can browse available products and place a cash-on-delivery order; shop staff manage products and orders through the protected dashboard or Django admin.

## Local setup

1. Create and activate a virtual environment, then run `pip install -r main/requirements.txt`.
2. Copy `.env.example` to `.env` and set development values as needed.
3. From `main/`, run `python manage.py migrate` and `python manage.py runserver`.

Run checks with `python manage.py check` and tests with `python manage.py test`.

## Production

Set `DEBUG=False`, a unique `SECRET_KEY`, and the deployed host in `ALLOWED_HOSTS`. Use the supplied build script to install dependencies, collect static files, and apply committed migrations. Serve Django via Gunicorn (not `runserver`). Cloudinary credentials are optional; without them, product uploads use local media storage, which must be persistent in production.

## Operations

Use `/admin_login/` with a Django superuser for the custom dashboard. Products can be marked unavailable to prevent public display and checkout. Order prices are stored as purchase-time totals.

### SQLite backup and restore

With the app stopped, copy `main/db.sqlite3` to a secure backup location. To restore, stop the app, retain a copy of the current database, replace `main/db.sqlite3` with the backup, and run `python manage.py migrate`. The database is ignored by Git and must not be used as a deployment backup mechanism.
