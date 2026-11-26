# Django backend (`main/`)

This folder is the **production deploy unit** for Lakshmi Broliers: WSGI app, migrations, static assets, templates, and platform config.

## Tech stack (this package)

- **Django 6.0.9** — apps: `home`, `store`, `orders`, `aboutus`, `admin_dashboard`
- **Gunicorn** — process model in `Procfile`
- **WhiteNoise** — hashed static files
- **Cloudinary** — product image storage (optional; falls back to filesystem)
- **PostgreSQL** via `DATABASE_URL` (SQLite when unset)
- **python-dotenv** — loads `main/.env`
- **Resend + Meta WhatsApp Cloud API + MSG91** — queued customer order notifications
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
| `RESEND_*`, `WHATSAPP_*`, `MSG91_*` | Email, WhatsApp and SMS order notifications |
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

### Order notifications

The live implementation uses Resend for email, Meta WhatsApp Cloud API for WhatsApp, and MSG91 Flow API for SMS. The notification worker must run separately; see the deployment section below. Provider credentials are optional during local development, but each channel will remain pending/retry until configured.


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
| `notifications.py` | Resend email and Meta WhatsApp Cloud API delivery helpers. |
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

The notification system uses a database-backed outbox. Order placement and subsequent order status transitions enqueue email, plus WhatsApp and SMS only when the customer explicitly checks each channel's separate consent box. A unique `(order, channel, event)` constraint prevents duplicate queue rows.

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
- `MSG91_AUTH_KEY`: MSG91 API auth key (secret).
- `MSG91_SMS_TEMPLATE_ID`: active MSG91 Flow template ID, mapped to your approved Indian DLT template.

The WhatsApp utility template must contain four body placeholders in this order: order ID, current order status, order total, and order-tracking URL. Configure and approve the template in Meta WhatsApp Manager before enabling live WhatsApp delivery.\n\nFor MSG91, create an SMS Flow template with three variables in this exact order: `VAR1` = order ID, `VAR2` = current status, `VAR3` = order total. For Indian numbers, map the template to your DLT-approved template ID and sender ID, verify it in MSG91, and make that version active. Never commit API keys or tokens.

### Deploy the worker

The web service only enqueues notifications. It does not send them itself. A separate long-running worker is required.

1. Deploy the web service first so the existing entrypoint applies migrations.
2. In Render, create a **Background Worker** using this repository, Docker runtime, Dockerfile path `main/Dockerfile`, and build context/root directory `main`.
3. Set the worker's start command to:

   ```bash
   python manage.py process_notifications --loop --interval 30 --limit 100
   ```

4. Copy the notification environment variables listed above to the worker. The worker and web service must use the same PostgreSQL `DATABASE_URL`; do not use separate SQLite files.
5. Deploy the worker and check its logs for `Notification worker started`.
6. Place a test order. Check Django Admin → Orders → Notification deliveries. Pending rows should be processed; successful sends become Sent, while provider errors remain visible in Last error and are retried.

The worker retries provider failures with increasing delays, up to six attempts. Email is skipped when the signed-in customer's account has no email address. WhatsApp and SMS are sent only when the customer checks their respective consent boxes. Meta requires an approved Utility template. MSG91 requires an active template mapped to the approved DLT template and sender ID in India. Resend production sending requires a verified sender domain; the default Resend test sender is not a production sender.

