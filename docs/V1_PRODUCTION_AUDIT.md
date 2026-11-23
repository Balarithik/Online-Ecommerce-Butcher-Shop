# AramCuts V1 Production Audit

## 1. Current Architecture

Django 6, Django templates, ORM, SQLite by default (with optional `DATABASE_URL`), WhiteNoise static delivery, optional Cloudinary media storage, and a custom superuser-only dashboard. The existing customer journey is product listing → product detail → direct buy-now checkout → order confirmation. There is no session cart or customer account/order-history feature in this V1.

## 2. Existing Features

Public home, about, product listing/detail, guest COD checkout, order confirmation, product/image administration, and staff order-status management.

## 3. Tested User Flows

Automated tests cover successful checkout, price tampering, invalid quantity, unavailable product, historical order totals, superuser dashboard protection, protected delete method, and unavailable product detail access. `check`, migrations, `collectstatic`, and `test` were run successfully.

## 4. Bugs Found

- Floating-point prices and quantities could introduce incorrect currency totals.
- A manually generated order ID could race under concurrent checkout.
- Products could not be marked unavailable, and checkout did not verify availability.
- Product deletion accepted GET/HTMX DELETE requests instead of a CSRF-protected POST.
- Cloudinary placeholders were hard-coded, and local settings forced `DEBUG=True`.
- The build script generated migrations during deployment.

## 5. Bugs Fixed

- Converted stored money and quantity values to validated decimal fields; total is calculated from the database product price only.
- Restored database-managed auto-increment order IDs.
- Added availability management and enforced it in public list/detail and checkout endpoints.
- Made deletion POST-only and retained CSRF protection.
- Added production environment configuration, secure cookies/HTTPS settings, optional Cloudinary configuration, and `.env.example`.
- Removed deployment-time `makemigrations`; committed migrations are applied by `migrate`.

## 6. Security Findings

No public order-detail endpoint exists, so no tested customer order-IDOR path exists. Custom dashboard and order status updates require a superuser. Checkout ignores client-submitted price and total values, validates quantity and mobile format, and does not accept unavailable products. Secret values are no longer embedded in settings.

## 7. Database Findings

Existing SQLite data was preserved and migrations `store.0005` and `orders.0010` applied successfully. New orders snapshot the product name, quantity, and purchase-time total; future product price changes do not alter past orders.

## 8. Admin Findings

Custom dashboard actions are superuser-only. Product availability can be set through the product add/edit forms. Product image uploads enforce extension validation and a 5 MB size limit.

## 9. UI/Mobile Findings

Templates retain the existing responsive Tailwind layout. This audit did not use a live browser/device emulator, so visual behavior at target viewport widths still needs a final shop-owner acceptance pass.

## 10. Deployment Findings

Static collection completes with WhiteNoise. Production mode requires `SECRET_KEY`; `DEBUG`, hosts, CSRF origins, HTTPS redirect, and Cloudinary are environment driven. Use Gunicorn or the platform’s WSGI command, not `runserver`.

## 11. Tests Added

Nine Django tests pass. They cover checkout integrity and validation, historical pricing, product availability, and administrative access/method protection.

## 12. Remaining Issues

Severity: MEDIUM
Issue: Duplicate checkout requests can create duplicate guest orders.
Impact: A double click or repeated POST can be recorded twice.
Recommended action: Add a small one-time checkout token/session guard if duplicate orders become operationally frequent.

Severity: LOW
Issue: Production deployment check recommends HSTS subdomain and preload settings.
Impact: The site is not eligible for browser preload and subdomains are not covered by HSTS.
Recommended action: Enable `SECURE_HSTS_INCLUDE_SUBDOMAINS` and preload only after confirming every current and future subdomain is HTTPS-only.

Severity: FUTURE
Issue: This V1 has no cart, categories, customer authentication, order history, or WhatsApp integration.
Impact: These capabilities are not available to customers.
Recommended action: Plan them as explicit V2 scope rather than adding them during production hardening.
