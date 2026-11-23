# Lakshmi Broliers (AramCuts V1)

Django + React ecommerce storefront for a local poultry shop. Customers browse products, manage a cart, create an account, and place cash-on-delivery orders. Shop staff manage catalog and orders through a protected admin dashboard.

**Live app (Render):** `https://lakshmi-broliers.onrender.com`

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | **Django 6.0.9**, Python 3.12+ (CI uses 3.14) |
| App server | **Gunicorn** (`main/Procfile`) |
| Database | **SQLite** locally; **PostgreSQL** via `DATABASE_URL` (`dj-database-url` + `psycopg`) in production |
| Static files | **WhiteNoise** (`CompressedManifestStaticFilesStorage`) |
| Media / images | **Cloudinary** (`django-cloudinary-storage`) when configured; local `MEDIA_ROOT` otherwise |
| Frontend (store) | Django templates + **Tailwind CSS CDN** + Material Symbols |
| Splash / warm-up UI | **React 19** + **Vite 8** (`SplashScreen/`) |
| Notifications | Optional **Twilio** SMS / WhatsApp |
| Auth | Django auth; customer signup/login + superuser admin dashboard |
| Hosting | **Render** and/or **AWS Elastic Beanstalk** |
| CI/CD | **GitHub Actions** (`.github/workflows/`) |

---

## Repository layout (what each top-level path is for)

| Path | Purpose |
|------|---------|
| `main/` | **Deployable Django project** (`manage.py`, apps, templates, static, Procfile). Zip/upload this folder for EB/Render. |
| `SplashScreen/` | React+Vite loading screen that health-checks the Django `/healthz/` endpoint, then redirects into the store. |
| `.github/workflows/` | CI tests and Elastic Beanstalk deploy automation. |
| `.elasticbeanstalk/` | EB CLI metadata at repo root (deploy target is still `main/`). |
| `.env.example` | Documented environment variables (copy → `main/.env` for local Django). |
| `.gitignore` | Ignores `.venv`, `.env`, `db.sqlite3`, `node_modules`, secrets, etc. |
| `README.md` | This file — stack, workflows, and file map. |
| `production_remediation_plan.md` | Status checklist of production/security remediation items. |
| `Lakshmi_Broilers_Security_UI_Production_Audit.md` | Full security/UI audit report. |
| `V1_PRODUCTION_AUDIT.md` | Earlier production audit notes. |

---

## Local development workflow

### Django (store + APIs)

1. Create a virtualenv and install deps:
   ```bash
   cd main
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy env file: from repo root, copy `.env.example` → `main/.env` and set at least `SECRET_KEY`, `DEBUG=True`, and optional Cloudinary/Twilio/WhatsApp values.
3. Migrate and run:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
4. Checks / tests:
   ```bash
   python manage.py check
   python manage.py test
   ```

### Splash screen (optional)

```bash
cd SplashScreen
npm install
# Set VITE_API_BASE_URL to your Django origin, e.g. http://127.0.0.1:8000
npm run dev
```

---

## Production workflow

1. Set `DEBUG=False`, a unique `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` (include every public HTTPS origin, e.g. `https://lakshmi-broliers.onrender.com`).
2. Prefer `DATABASE_URL` (Postgres). SQLite is wiped on ephemeral hosts.
3. Configure Cloudinary for persistent product images.
4. For Render with the service root directory set to `main`, use build command `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput` and start command `gunicorn main.wsgi:application`. Do not run `makemigrations` during deployment.
5. Serve with Gunicorn (`main/Procfile`), not `runserver`.

### Render

- Root / start command should target `main/` (Gunicorn `main.wsgi:application`).
- Set `DEBUG=False`, `SECRET_KEY`, `ALLOWED_HOSTS=lakshmi-broliers.onrender.com`, `CSRF_TRUSTED_ORIGINS=https://lakshmi-broliers.onrender.com`, `DATABASE_URL`, and either `CLOUDINARY_URL` or the three `CLOUDINARY_*` values. Use the exact active API key/secret pair from the same Cloudinary product environment; do not use the values in old local files or Docker images. Set `WHATSAPP_NUMBER` as required.
- Ensure `CSRF_TRUSTED_ORIGINS` lists the exact Render URL.

### AWS Elastic Beanstalk

Deploy the **`main/`** folder only (it contains `manage.py`, `Procfile`, `requirements.txt`, `.ebextensions/`).

1. Python 3.12 Amazon Linux 2023 environment.
2. Upload a zip of `main/`, or from `main/` run `eb init` / `eb create` / `eb deploy`.
3. Set console env properties (never commit secrets):

```text
DEBUG=false
SECRET_KEY=<stable-secret>
ALLOWED_HOSTS=<env-url>.elasticbeanstalk.com,your-domain.com
CSRF_TRUSTED_ORIGINS=https://<env-url>.elasticbeanstalk.com,https://your-domain.com
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
# Or set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET separately.
WHATSAPP_NUMBER=
```

GitHub Actions deploy: [`.github/workflows/deploy-elastic-beanstalk.yml`](.github/workflows/deploy-elastic-beanstalk.yml). Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`. Optional vars: `AWS_REGION`, `EB_APPLICATION_NAME`, `EB_ENVIRONMENT_NAME`.

CI on every push/PR to `main`: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs `manage.py check` and `manage.py test`.

---

## Key product flows

- **Browse / cart:** Storefront templates + `AramCart` JS in `base.html`; cart APIs under `orders/`.
- **Account:** `/signup/`, `/login/`, `/account/` — CSRF-protected; signup/login use `@never_cache` + `@ensure_csrf_cookie`.
- **Checkout:** Requires login; server-side cart, address validation, idempotent `placement_token`.
- **Staff:** `/admin_login/` → `/admin_dashboard/` (superuser only); product CRUD + Cloudinary uploads.
- **Health:** `GET /healthz/` → `{"status":"ok"}` (used by SplashScreen).

---

## Operations notes

- Dashboard login: Django **superuser** at `/admin_login/`.
- Mark products unavailable to hide them from catalog/checkout.
- Order prices are stored as purchase-time totals.
- SQLite backup: stop the app, copy `main/db.sqlite3`; restore by replacing the file and running `migrate`. Do not use SQLite as a production backup strategy on Render/EB.

More detail:

- Django/Cloudinary/Twilio env: [`main/README.md`](main/README.md)
- Splash screen: [`SplashScreen/README.md`](SplashScreen/README.md)
