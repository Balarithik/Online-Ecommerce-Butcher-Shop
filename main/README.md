# Django backend (`main/`)

This folder is the **production deploy unit** for Lakshmi Broliers: WSGI app, migrations, static assets, templates, and platform config.

## Tech stack (this package)

- **Django 6.0.9** — apps: `home`, `store`, `orders`, `aboutus`, `admin_dashboard`
- **Gunicorn** — process model in `Procfile`
- **WhiteNoise** — hashed static files
- **Cloudinary** — product image storage (optional; falls back to filesystem)
- **PostgreSQL** via `DATABASE_URL` (SQLite when unset)
- **python-dotenv** — loads `main/.env`
- **Twilio** (optional) — order SMS / WhatsApp in `orders/notifications.py`
- **Pillow** — admin image validation before Cloudinary upload

## Environment

Copy repo-root `.env.example` to `main/.env` (never commit `.env`).

| Variable | Use |
|----------|-----|
| `SECRET_KEY` | Django secret (required when `DEBUG=False`) |\n| `DJANGO_SUPERUSER_USERNAME` | Initial admin username (required for automatic bootstrap) |\n| `DJANGO_SUPERUSER_EMAIL` | Initial admin email (required for automatic bootstrap) |\n| `DJANGO_SUPERUSER_PASSWORD` | Initial admin password (required for automatic bootstrap) |
| `DEBUG` | `True` locally; `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins with scheme (e.g. `https://lakshmi-broliers.onrender.com`) |
| `DATABASE_URL` | Postgres URL in production |
| `WHATSAPP_NUMBER` | Shop WhatsApp (digits, country code first) |
| `CLOUDINARY_*` / `CLOUDINARY_URL` | Product image uploads |
| `TWILIO_*` | Optional order notifications |
| `SECURE_SSL_REDIRECT` | HTTPS redirect when not DEBUG |

### Cloudinary

Either:

```dotenv
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

or:

```dotenv
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

Admin create/edit uploads go through a signed Django endpoint (`upload_product_image`). JPG/PNG/WebP up to 5 MB; public IDs stored under `products_images/`.

### Twilio (optional)

```dotenv
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_SMS_FROM=+1...
TWILIO_WHATSAPP_FROM=whatsapp:+1...
TWILIO_WHATSAPP_CONTENT_SID=HX...
ORDER_NOTIFICATION_COUNTRY_CODE=91
```

Leave blank to skip external notifications; order placement still works.

## Commands

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver          # local only
python manage.py check
python manage.py test
python manage.py collectstatic      # production / WhiteNoise
```

Production entry: Gunicorn via `Procfile`. Build helper: `build.sh` (install dependencies → collectstatic). Apply committed migrations with `python manage.py migrate --noinput` during deployment. The `bootstrap_superuser` management command creates the initial superuser when all three `DJANGO_SUPERUSER_*` variables are set. The native Render Procfile and Docker entrypoint both run this command on startup; it is safe on restarts and never resets an existing account's password.

---

## File & folder map

### Root of `main/`

| File / folder | Purpose |
|---------------|---------|
| `manage.py` | Django CLI entrypoint. |
| `requirements.txt` | Pip dependencies for deploy and local install. |
| `pyproject.toml` / `uv.lock` | Optional uv/project metadata; pip still uses `requirements.txt`. |
| `Procfile` | Gunicorn web process for Render/EB/Heroku-style hosts. |
| `build.sh` | Install dependencies and collect static files; does not generate migrations or create accounts. |
| `.python-version` | Preferred Python version for platform tooling. |
| `.env` | Local secrets (gitignored). |
| `.ebignore` | Files excluded from EB bundles. |
| `.ebextensions/01-django.config` | EB container options / Django deploy hooks. |
| `.elasticbeanstalk/config.yml` | Local EB CLI environment linkage. |
| `db.sqlite3` | Local SQLite DB (gitignored; not for production). |
| `README.md` | This document. |
| `static/` | Project static sources (icons, CSS assets) collected into `staticfiles/`. |
| `staticfiles/` | Output of `collectstatic` (served by WhiteNoise). |


### Project package `main/main/`

| File | Purpose |
|------|---------|
| `settings.py` | Apps, middleware, DB, CSRF/session security, Cloudinary, WhiteNoise, timezone `Asia/Kolkata`. |
| `urls.py` | Root URLconf: healthz, admin, dashboard, about, products, orders, home. |
| `wsgi.py` | WSGI application for Gunicorn. |
| `asgi.py` | ASGI entry (unused by current Procfile). |
| `views.py` | `/healthz/` and custom `csrf_failure` view. |
| `context_processors.py` | Exposes `settings` to all templates (e.g. WhatsApp number). |
| `templates/` | All HTML templates (base, home, store, orders, accounts, admin, about). |
| `templates/base/base.html` | Global chrome, cart drawer, CSRF sync, Tailwind config. |
| `templates/accounts/` | Signup, login, account management. |
| `templates/orders/` | Cart, checkout, confirmation, my orders. |
| `templates/store/` | Product list / detail. |
| `templates/admin/` | Custom staff dashboard UI (not Django admin skin only). |
| `templates/aboutus/` | About page. |
| `templates/403_csrf.html` | Friendly page when CSRF check fails. |
| `media/` | Local media root when Cloudinary is off. |

### App: `home/`

| File | Purpose |
|------|---------|
| `views.py` | Home page; customer login/signup/logout/account/delete (CSRF-safe auth). |
| `forms.py` | Signup, profile, address forms. |
| `models.py` | `CustomerProfile`, `CustomerAddress`. |
| `urls.py` | `/`, `/login/`, `/signup/`, `/account/`, etc. |
| `admin.py` | Registers customer models in Django admin. |
| `tests.py` | Auth, account, health, CSRF regression tests. |
| `migrations/` | Schema history for customer models. |

### App: `store/`

| File | Purpose |
|------|---------|
| `models.py` | `Products` (images, price, availability). |
| `views.py` | Product listing / detail / buy-now routes. |
| `urls.py` | Under `/products/`. |
| `admin.py` | Product admin registration. |
| `tests.py` | Store view tests. |
| `migrations/` | Product schema (images, price, availability). |

### App: `orders/`

| File | Purpose |
|------|---------|
| `models.py` | `Order`, `OrderItem`, `Cart`, `CartItem`, placement token. |
| `views.py` | Cart APIs, checkout, place order, my orders, confirmation. |
| `forms.py` | `OrderForm` with server-side address/payment/cut/slot validation. |
| `notifications.py` | Twilio SMS/WhatsApp helpers. |
| `urls.py` | Under `/orders/` and checkout paths used by store. |
| `admin.py` | Order admin. |
| `tests.py` | Cart, checkout, idempotency, auth gating tests. |
| `migrations/` | Order/cart evolution including multi-item and tokens. |

### App: `admin_dashboard/`

| File | Purpose |
|------|---------|
| `views.py` | Superuser dashboard, products CRUD, Cloudinary upload, order updates, CSRF-safe admin login. |
| `forms.py` | Product forms with Cloudinary public ID fields. |
| `urls.py` | Under `/admin_dashboard/`. |
| `tests.py` | Dashboard auth, CSRF, UI/layout tests. |
| `models.py` | Placeholder (logic uses `store` / `orders` models). |

### App: `aboutus/`

| File | Purpose |
|------|---------|
| `views.py` / `urls.py` | About page route. |
| `models.py` / `migrations/` | Any about-page content models. |
| `tests.py` | About page tests. |

---

## CSRF / auth notes

Customer `/signup/` and `/login/` (and admin login) use `@never_cache` + `@ensure_csrf_cookie` so browsers/proxies do not cache a stale CSRF form token. Production must set `CSRF_TRUSTED_ORIGINS` to the public HTTPS origin. `base.html` also re-syncs hidden CSRF fields from the `csrftoken` cookie on `pageshow`/`submit` (helps mobile back-forward cache).

## Customer order notifications

The notification system uses a database-backed outbox. Order placement and every subsequent order status transition enqueue one email delivery and, only when the customer explicitly checks the WhatsApp consent box, one WhatsApp delivery. A unique `(order, channel, event)` constraint prevents duplicate queue rows.

### Render environment variables

Set these in the web service and notification worker service:

- `RESEND_API_KEY`: Resend API key (secret).
- `RESEND_FROM_EMAIL`: verified sender, e.g. `Lakshmi Broilers <orders@your-verified-domain.in>`.
- `NOTIFICATION_SITE_URL`: public HTTPS base URL, e.g. `https://lakshmi-broliers.onrender.com`.
- `WHATSAPP_CLOUD_ACCESS_TOKEN`: Meta permanent/system-user token (secret).
- `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp Cloud API phone-number ID.
- `WHATSAPP_ORDER_TEMPLATE`: approved utility template name.
- `WHATSAPP_TEMPLATE_LANGUAGE`: approved template language code (default `en`).
- `WHATSAPP_GRAPH_API_VERSION`: supported Graph API version (default `v22.0`).
- `ORDER_NOTIFICATION_COUNTRY_CODE`: default `91` for India.

The WhatsApp utility template must contain four body placeholders in this order: order ID, current order status, order total, and order-tracking URL. Configure and approve the template in Meta WhatsApp Manager before enabling live WhatsApp delivery. Never commit API keys or tokens.

### Deploy the worker

1. Deploy the web service first so migration `0007_notification_delivery` runs through the existing entrypoint.
2. In Render, create a Cron Job using the same repository, Dockerfile `main/Dockerfile`, and build context `main`.
3. Set its command to `python manage.py process_notifications --limit 100` and schedule it every minute.
4. Copy the same notification environment variables to the cron job. The worker and web service must use the same persistent PostgreSQL database; do not use separate SQLite files.
5. Verify a test order produces an email delivery row and that the worker changes it to Sent. Test WhatsApp only after explicit customer consent and Meta template approval.

The queue retries provider failures with increasing delays, up to six attempts. Review and manually investigate terminal Failed entries in Django Admin → Orders → Notification deliveries. Email is skipped when the account has no email address; WhatsApp is never sent without recorded order-level consent.