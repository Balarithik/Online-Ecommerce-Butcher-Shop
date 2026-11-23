# Lakshmi Broilers / AramCuts — Source-Code Security, UX, and Production Audit

**Review date:** 10 October 2026  
**Repository:** [Balarithik/Online-Ecommerce-Butcher-Shop](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/tree/main)  
**Reviewed branch:** `main`  
**Reviewed commit:** `810267aa3d4991e301e7a56bbfa7f344c24bbd7a`  
**Application stack found:** Django 6, Django templates, SQLite by default / optional `DATABASE_URL`, WhiteNoise, optional Cloudinary media storage, plus a separate React/Vite splash-screen app.

## 1. Executive summary

This repository contains useful foundations: Django’s CSRF middleware and authentication, superuser-only guards on custom administration pages, validated decimal fields for order quantity/price, server-side price calculation, availability checks, product-image validation, and tests for several important cases.

However, I found **two urgent privacy/security issues in the source** and multiple production-blocking business-logic and reliability problems. The most important issues are:

1. **A database-style JSON export is committed to a public repository.** It includes an administrator password hash, a serialized session record, and order/customer contact and delivery details. Treat it as exposed data.
2. **The unauthenticated order-history lookup permits searching by a substring of a phone number.** A non-numeric value can normalize to an empty string, which can match every order. The template then displays customer/order details.
3. **The visible multi-item cart only sends the first cart item to checkout.** Customers can see a basket total for several products but the backend creates a single-product order.
4. **The order confirmation/history templates simulate live progress and delivery promises that do not match the persisted order status.** New orders are saved as `pending`, while the UI says preparation has started and displays fixed “live tracking” stages and countdown text.
5. **The React splash screen silently falls back to `http://localhost:8000` and retries forever.** A missing production environment variable can leave visitors stuck on the splash screen.
6. **Public marketing pages contain several specific certification, hygiene, temperature, sourcing and delivery claims that are not substantiated in the repository and contradict each other.** These should be verified or removed before launch.
7. **The pinned Django version is behind the latest security patch release available on the review date.** Django 6.0.9 was released on 6 October 2026 and addresses multiple security issues. [Official release notes](https://docs.djangoproject.com/en/dev/releases/6.0.9/).

### Overall disposition

**Do not treat the current public repository/deployment as production-ready until the data dump and unauthenticated order disclosure are addressed.** Even after those two urgent fixes, checkout/cart integrity, misleading order-status UI, splash-screen configuration, and unsupported public claims need resolution before the site is promoted to customers.

This is a **source-code review**, not a formal penetration-test certificate. I inspected files available in the public GitHub repository. The live URL `https://lakshmi-broliers-static.onrender.com/` could not be retrieved by the web inspection environment (`Cache miss`), so I could not verify the currently deployed instance, TLS/header responses, actual network routing, or execute end-to-end browser tests against it. Source-confirmed weaknesses below are therefore not presented as proof that every condition is currently reachable on that exact live hostname.

---

## 2. Findings and remediation priorities

Severity guide: **P0 Critical** = act immediately; **P1 High** = fix before public ordering; **P2 Medium** = fix before a dependable production launch; **P3 Low** = cleanup / hardening.

### P0-1 — Public repository contains a database-style export with sensitive records

**Severity:** Critical  
**Confidence:** Confirmed in the public source tree  
**Evidence:** [`main/data.json`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/data.json) (the export is serialized as a single long line).

The file contains Django records including an administrator account’s password hash, a serialized session record, customer/order records and delivery details. I have intentionally not reproduced any actual values in this report. The session timestamp in the dump appears old, but the personal/order records and password hash remain exposed in public repository history.

**Impact:** Customer privacy exposure, offline password-guessing risk against the password hash, and possible reuse of any still-valid secrets or sessions if the dump overlaps with a live environment. A password hash is not a plaintext password, but publishing it creates avoidable risk.

**Required remediation:**

1. Immediately remove the export from the current repository tree. Do not replace it with another live database dump.
2. **Purge the file from Git history** across branches/tags using a history-rewrite tool such as `git filter-repo` or BFG. A deletion commit alone does not remove prior public commits, existing clones or forks. Coordinate the rewrite and force-push carefully.
3. Reset administrator credentials and invalidate active application sessions in the deployed environment. Rotate other credentials if investigation shows they were exposed. Do not include any live records in test fixtures.
4. Review hosting/database access logs and determine whether the exposed records correspond to real customers. Assess applicable privacy, incident-response and notification obligations with an appropriate professional.
5. Add `main/data.json` (and similar exports/dumps) to `.gitignore`; add a repository secret/data-leak scanning check.
6. If sample data is needed, create a sanitized, synthetic fixture with fake names, addresses, phone numbers, sessions and password hashes.

### P0-2 — Public order lookup by partial phone number exposes order/customer information

**Severity:** Critical  
**Confidence:** Confirmed in source logic; deployment reachability not tested  
**Evidence:** [`main/orders/views.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/views.py#L154-L172), [`main/main/templates/orders/my_orders.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/orders/my_orders.html#L14-L160).

`my_orders()` does not require login before looking up orders. When a `mobile` query parameter is supplied, it strips non-digits and filters using `mobile__icontains`. This is a substring search, not proof that the requester owns an order. A query such as a short digit sequence can match many records; a non-empty alphabetic query normalizes to an empty string and can match all phone values because the lookup becomes effectively `icontains=''`. The template renders customer names, phone numbers, delivery address, product, price and order status.

**Impact:** An unauthenticated visitor may enumerate customer/order information. This is a broken-access-control and personal-data disclosure issue, consistent with OWASP’s A01:2025 category. [OWASP A01: Broken Access Control](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/).

**Required remediation:**

- Remove public order lookup by phone substring.
- For authenticated customers, return only `Order.objects.filter(user=request.user)`.
- If guest order tracking must remain, use an unguessable order-access token and/or a properly verified OTP flow; do not treat knowing a phone number as ownership proof.
- Rate-limit lookup/OTP attempts and return generic responses that do not confirm whether a phone number has orders.
- Add tests proving anonymous users cannot enumerate orders and customer A cannot view customer B’s order. Include short, blank-after-normalization, alphabetic and partial-phone test cases.

### P1-1 — Cart presents multiple items but checkout submits only the first item

**Severity:** High  
**Confidence:** Confirmed in source  
**Evidence:** [`main/main/templates/base/base.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/base/base.html#L490-L670), [`main/orders/views.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/views.py#L64-L124), [`main/orders/models.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/models.py).

The JavaScript cart stores items in `localStorage`, totals all items in the browser, and `proceedToCheckout()` navigates using only `items[0]`. The Django order model represents a single product line, and the backend creates an order for the one product ID in the route. Consequently, the displayed basket can contain multiple products while the submitted order includes only the first product.

**Impact:** Customers may believe they purchased multiple products when only one is recorded. The displayed total can disagree with the saved order, causing disputes and lost sales.

**Required remediation:**

- Best fix: implement server-validated multi-item order lines (`Order` + `OrderItem`), re-fetch every product from the database, validate each quantity/availability, and calculate the total server-side in one transaction.
- If that scope is intentionally deferred, do not expose the multi-item cart as if it can be checked out; restrict checkout to a single product and clearly communicate that constraint.
- Add an end-to-end test with two distinct products that verifies both lines and the final total.

### P1-2 — Order confirmation and order-history UI claims fake/live progress

**Severity:** High  
**Confidence:** Confirmed in source  
**Evidence:** [`main/orders/views.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/views.py#L100-L124), [`main/main/templates/orders/order_confirmation.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/orders/order_confirmation.html#L30-L110), [`main/main/templates/orders/my_orders.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/orders/my_orders.html#L70-L115).

The order view saves a new order with status `pending`. The confirmation template nevertheless says the order is already being prepared, shows a fixed “Today in ~45 Minutes” arrival message, “On Schedule,” and “Live Tracking,” and renders fixed stages such as order confirmed/cutting/packing. The history page similarly renders a static stepper for any non-cancelled/non-delivered status rather than deriving each step from the actual status.

**Impact:** Customers receive inaccurate fulfilment information and may rely on a delivery promise that is not based on real operational data. It also damages trust when the shop has not yet accepted the order.

**Required remediation:**

- Render the actual persisted order status.
- For `pending`, say “Order received — awaiting shop confirmation.”
- Display ETA only when the shop has configured a real estimate or an actual delivery slot has been accepted.
- Remove “live” language and animations unless status updates are genuinely refreshed from the backend.
- Keep the timeline state machine aligned with the `Order.status_choices` and test every status.

### P1-3 — Splash screen can permanently stall if production API URL is missing or unreachable

**Severity:** High  
**Confidence:** Confirmed configuration/failure-path issue  
**Evidence:** [`SplashScreen/src/App.jsx`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/SplashScreen/src/App.jsx#L1-L100), [`SplashScreen/index.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/SplashScreen/index.html), [root `.env.example`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/.env.example).

`MAIN_APP_URL` falls back to `http://localhost:8000` if `VITE_API_BASE_URL` is not set. In a visitor’s browser, `localhost` refers to the visitor’s own device, not the deployed Django backend. Failed health checks are retried every two seconds indefinitely and there is no visible terminal error/retry/fallback action. The loader can therefore remain stuck instead of explaining the issue. The root `.env.example` documents Django variables but does not document the splash app’s `VITE_API_BASE_URL`. Also, `SplashScreen/index.html` uses a backslash-based favicon path (`\src\assets\logo.png`) that is not a reliable production asset URL.

**Required remediation:**

- Remove the localhost fallback from production builds. Fail the build or show a clear configuration error if `VITE_API_BASE_URL` is not set.
- Add `SplashScreen/.env.example` and deployment documentation for the separate frontend build variable.
- Add an elapsed-time threshold, visible retry control, and a safe “Open store”/fallback action. Do not retry forever without user feedback.
- Distinguish app liveness from readiness; if checkout depends on the database, the readiness check should verify the dependency required to serve the main site.
- Fix the favicon reference using a public asset path or Vite-imported asset.
- Test success, 404, CORS failure, timeout, server down, missing env variable and mobile connection loss.

### P1-4 — Public pages contain unsupported and contradictory food/business claims

**Severity:** High before public launch  
**Confidence:** Confirmed that the claims are in source; factual substantiation was not provided  
**Evidence:** [`main/main/templates/aboutus/aboutus.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/aboutus/aboutus.html#L10-L110), [`main/main/templates/home/index.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/home/index.html), [`main/main/templates/base/base.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/base/base.html#L1-L30), [`SplashScreen/src/App.jsx`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/SplashScreen/src/App.jsx#L185-L280).

Examples in the source include “Since 1988,” “ISO Certified Facility,” “Lab Certified,” “top 1%” hygiene language, a claimed 12-hour sterilization process, hormone-free/chemical-free claims, a “100% Halal” badge, fixed 45–60 minute delivery claims, and vacuum-sealing/cold-storage claims. The About page states a constant 22°C logistics environment, while the splash screen claims 0–4°C packing. The home page links to “Our 5-Stage Hygiene,” but the About page visibly contains four process cards. The About page also contains a generic-looking address that conflicts with the Uchipuli/Ramanathapuram description used elsewhere. I have not been given evidence to verify any of these claims.

**Impact:** Unsupported certification/sourcing/health/safety claims and contradictory handling information can mislead customers and materially harm credibility. Temperature claims are particularly important for a perishable-food business and must match actual handling practice and applicable food-safety advice.

**Required remediation:**

- Audit every public claim with the business owner and supporting documentation.
- Remove or replace unsubstantiated certificates, “top 1%,” years-in-business, health/chemical claims, cold-chain claims and delivery guarantees.
- Replace the generic address with the verified business address and confirm every phone/WhatsApp number.
- State the real delivery area and ETA based on operations rather than a universal promise.
- Do not advertise a specific temperature unless it accurately describes the process and complies with applicable guidance.
- Fix the “5-stage” vs four-card mismatch and use actual shop photographs where available.

### P1-5 — Production configuration defaults to `DEBUG=True` unless the environment is explicitly set

**Severity:** High / conditional on deployment configuration  
**Confidence:** Confirmed in settings; one deployment config does explicitly set `DEBUG=false`  
**Evidence:** [`main/main/settings.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/settings.py#L28-L55), [`.env.example`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/.env.example), [`main/.ebextensions/01-django.config`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/.ebextensions/01-django.config).

The settings file defaults `DEBUG` to `True`, and the development fallback secret is allowed when `DEBUG=True`. The Elastic Beanstalk config shown in the repository explicitly sets DEBUG to false, which is good, but any deployment that does not apply that configuration and omits the environment variable falls back to debug mode. `ALLOWED_HOSTS` also has broad default suffixes such as `.onrender.com` and `.elasticbeanstalk.com`; a production override with exact known hostnames is safer.

**Required remediation:**

- Use a fail-closed production default (`DEBUG=False`) and explicitly set debug mode only in local development.
- Fail startup in production if `SECRET_KEY` is missing or uses a known development fallback.
- Set `ALLOWED_HOSTS` to the exact production hostname(s) in the actual runtime environment.
- Configure and verify CSRF trusted origins, HTTPS redirect, secure session/CSRF cookies, HSTS and the proxy HTTPS header for the actual deployment topology.
- Run `python manage.py check --deploy` against the production environment configuration, then fix applicable warnings.

### P1-6 — Pinned Django version is behind a recent security patch release

**Severity:** High  
**Confidence:** Confirmed dependency pin  
**Evidence:** [`main/requirements.txt`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/requirements.txt) pins `Django==6.0.6`.

Django 6.0.9 was released on 6 October 2026 and fixes several security issues, including moderate-severity issues. The current pinned version predates that release. [Django 6.0.9 release notes](https://docs.djangoproject.com/en/dev/releases/6.0.9/) and [Django security release archive](https://docs.djangoproject.com/en/6.0/releases/security/).

**Required remediation:**

- Upgrade to the latest compatible supported patch release (6.0.9 as of this review), review release notes, rebuild the deployment environment and rerun the complete test suite.
- Run `pip-audit` or an equivalent dependency scanner, review all findings, and do not blindly upgrade unrelated packages.
- Align `main/.python-version`, `main/pyproject.toml` (`requires-python >=3.14`) and the README’s AWS instructions (Python 3.12). Choose and test one supported runtime across local development, CI and production.

### P2-1 — Client-side cart uses unsafe HTML interpolation

**Severity:** Medium hardening issue; exploitability depends on a malicious/untrusted product value reaching the sink  
**Confidence:** Confirmed dangerous DOM construction pattern; no live XSS exploit attempted  
**Evidence:** [`main/main/templates/base/base.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/base/base.html#L590-L665), [`main/main/templates/home/index.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/home/index.html).

The cart writes a toast with `toast.innerHTML` using a message that includes the product name, and rebuilds cart rows with `itemsContainer.innerHTML` by interpolating name, image URL, price, quantity and ID from `localStorage`. Those values are browser-editable and may originally come from server product data. HTML interpolation is a fragile pattern and can become XSS if untrusted or malicious product content reaches it. This audit did not demonstrate a remote exploit in the deployed site.

**Required remediation:**

- Build cart nodes using DOM APIs and set text with `textContent`.
- Validate the local cart schema (integer product ID, bounded positive quantity, allowed image URL, string length bounds) before rendering.
- Do not put arbitrary values into inline `onclick` or HTML attributes.
- Keep prices from localStorage display-only; continue recalculating order values from the database on the server.
- Add tests using product names containing quotes/markup and tampered localStorage entries.

### P2-2 — Payment method, cut preference and delivery slot are accepted as arbitrary POST text

**Severity:** Medium  
**Confidence:** Confirmed in source  
**Evidence:** [`main/orders/views.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/views.py#L80-L100), [`main/orders/forms.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/forms.py), [`main/orders/models.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/models.py).

The order view reads `payment`, `delivery_slot` and `cut_preference` directly from `request.POST` and persists those strings. The form/model choices do not restrict all these values to the options presented in the UI. A crafted request can store arbitrary method/slot text. There is no payment gateway shown in this repository; “UPI / QR Code on Delivery” appears to be a payment-on-delivery option, not verified online payment.

**Required remediation:**

- Validate and whitelist server-side payment methods, delivery slots and cut preferences.
- Use cleaned form data rather than raw POST values.
- Label UPI/QR accurately as payment on delivery unless a real payment provider is integrated and server-side verified.
- Do not set any paid status based on a client-submitted method string.

### P2-3 — Checkout’s individual address fields are not independently required or server-validated

**Severity:** Medium  
**Confidence:** Confirmed in template/form structure  
**Evidence:** [`main/main/templates/orders/checkout.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/orders/checkout.html#L20-L260), [`main/orders/forms.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/forms.py).

The house/street/area/landmark/pincode controls are JavaScript-only inputs without their own form `name` attributes. JavaScript concatenates them into a single hidden `address` field. The backend validates only that the combined address string is non-empty, not that the expected components exist or that a pincode is valid. The hidden address relies on `syncFullAddress()` firing through UI input events; a user can bypass the component-level checks by crafting a request.

**Required remediation:**

- Add named server-bound fields or a Django form that validates the required address components individually.
- Validate a six-digit Indian PIN code if it is a business requirement, and confirm delivery coverage server-side.
- Keep frontend validation for usability, but make server validation authoritative.
- Test empty/missing house, street, area and pincode, with JavaScript disabled and with a handcrafted POST.

### P2-4 — Repeated checkout submission can create duplicate orders

**Severity:** Medium  
**Confidence:** Likely from the current POST flow; not load-tested  
**Evidence:** [`main/orders/views.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/views.py#L64-L145).

A successful order is saved and rendered directly from the POST response. There is no one-time checkout token or idempotency guard visible in the order flow. Refreshing/repeating a POST can create another order for the same purchase attempt.

**Required remediation:**

- Use POST-Redirect-GET after saving an order.
- Add a small one-time checkout token/idempotency key stored server-side, scoped to the session/order attempt, and enforce uniqueness.
- Disable the submit button after the first request for UX, but do not rely on frontend locking as the security/control mechanism.

### P2-5 — Admin dashboard’s “revenue” includes orders that have not been delivered

**Severity:** Medium business-accuracy issue  
**Confidence:** Confirmed calculation  
**Evidence:** [`main/admin_dashboard/views.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/admin_dashboard/views.py#L145-L165).

`total_revenue` sums all orders except those marked `cancelled`, including `pending`, `preparing` and `out_for_delivery` orders. For COD/manual UPI-on-delivery, this can represent order value rather than collected revenue.

**Required remediation:**

- Separate metrics: order value, delivered sales and actually collected/settled payments.
- Until payment collection is recorded in the data model, label the figure “non-cancelled order value” rather than “revenue.”
- Add tests for the dashboard totals by status.

### P2-6 — Production Tailwind Play CDN and third-party assets are loaded at runtime

**Severity:** Medium performance/availability/supply-chain hardening  
**Confidence:** Confirmed source configuration  
**Evidence:** [`main/main/templates/base/base.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/base/base.html#L1-L30), [`SplashScreen/index.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/SplashScreen/index.html).

The Django base template and splash page load Tailwind through `cdn.tailwindcss.com`, along with external Google Fonts/Material Symbols. Runtime utility-CSS compilation is intended for development rather than a hardened production asset pipeline. Availability or policy changes at third-party hosts can affect rendering, and remote scripts complicate Content Security Policy.

**Required remediation:**

- Compile/minify CSS at build time and serve versioned static assets using the existing static pipeline.
- Keep only needed icons/fonts; consider self-hosting permitted font assets if appropriate.
- Remove unused template code/dependencies and test pages with third-party font/CDN requests blocked.

### P2-7 — Brand/support information is inconsistent and some controls are decorative/non-functional

**Severity:** Medium UX/operations  
**Confidence:** Confirmed inconsistent source strings; real business values need owner verification  
**Evidence:** [`main/main/templates/aboutus/aboutus.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/aboutus/aboutus.html), [`main/main/templates/orders/order_confirmation.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/orders/order_confirmation.html#L180-L220), [`main/main/templates/orders/my_orders.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/orders/my_orders.html#L130-L155), [`main/main/templates/base/base.html`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/base/base.html).

A WhatsApp number is hard-coded in order/support templates and differs from the phone numbers shown on the About page. The About page uses a generic-looking street address despite naming Uchipuli/Ramanathapuram elsewhere. Some UI includes permanent free-delivery, 45-minute, vacuum-sealed and “chemical-free” messaging. These need verification and a single source of truth. One image uses `data-alt` rather than a real `alt` attribute. The project’s customer-facing brand says “Lakshmi Broliers,” while repository README and localStorage naming use “AramCuts”; the separate splash assets include an AramCuts-named file while its displayed brand says Lakshmi Broliers.

**Required remediation:**

- Store the actual support/WhatsApp number, address, shop hours, delivery zone, fees and ETA in one configuration location; use it throughout templates.
- Verify the intended legal/trading name and keep README, favicon, splash screen, cart labels and page metadata consistent.
- Replace decorative buttons with valid `tel:`/`https://wa.me/` links or real forms.
- Correct image alt text, keyboard behavior, form labels and reduced-motion behavior.
- Remove unsupported guarantees and unnecessary pulsing/animated badges; prioritize useful information and genuine shop imagery.

### P2-8 — Deployment workflow does not run tests and uses mutable action tags

**Severity:** Medium supply-chain/quality-gate hardening  
**Confidence:** Confirmed workflow configuration  
**Evidence:** [`.github/workflows/deploy-elastic-beanstalk.yml`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/.github/workflows/deploy-elastic-beanstalk.yml), [branch metadata](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/branches).

The workflow deploys on each push to `main` and packages/deploys without running the Django test suite, deployment checks, dependency audit or frontend build/lint checks. Actions use version tags (`actions/checkout@v4`, `einaregilsson/beanstalk-deploy@v22`) rather than immutable full commit SHAs. The workflow also sets `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION: true`. GitHub recommends pinning actions to full-length SHAs for immutable references. [GitHub Secure Use reference](https://docs.github.com/en/actions/reference/security/secure-use).

The repository’s `main` branch is also reported by GitHub as unprotected, with no required status checks. This review does not indicate that a workflow action has been compromised; it identifies a preventable supply-chain and release-control risk.

**Required remediation:**

- Add CI before deploy: install dependencies, run `python manage.py check`, migration consistency check, tests, dependency audit and the SplashScreen build/lint.
- Separate validation from deployment; deploy only after required checks pass.
- Pin third-party actions to verified full commit SHAs, remove the insecure-node-version override and update old actions.
- Enable branch protection/rules requiring checks and review where practical.
- Prefer short-lived AWS OIDC credentials if the deployment setup supports them; otherwise use narrowly scoped credentials and rotation.

### P3-1 — Tracked virtual-environment executable and generated staticfiles add repository noise

**Severity:** Low / maintenance  
**Confidence:** Confirmed in tree  
**Evidence:** [`.venv/Scripts/python.exe`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/tree/main/.venv), [`main/staticfiles/`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/tree/main/main/staticfiles), [`.gitignore`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/.gitignore).

A Python interpreter binary from a local virtual environment is tracked. Generated Django staticfiles are also committed. `.gitignore` does not currently exclude `.venv/` at repository root. These files enlarge the repository and make build artifacts harder to distinguish from source.

**Remediation:** Remove the environment binary from Git tracking, add `.venv/` and generated `main/staticfiles/` to ignore rules if they are build artifacts, and use `collectstatic` during deployment. Do not delete required source assets from `main/static/`.

### P3-2 — Timezone and runtime documentation mismatch

**Severity:** Low/Medium operations  
**Confidence:** Confirmed configuration mismatch  
**Evidence:** [`main/main/settings.py`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/settings.py#L150-L165), [`main/.python-version`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/.python-version), [`main/pyproject.toml`](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/pyproject.toml), [README](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/README.md).

Django is configured with `TIME_ZONE='UTC'`, even though the shop operates in India. That can make order times look offset if templates show local-facing order timestamps without conversion. The Python metadata specifies 3.14 while the README’s Elastic Beanstalk steps say Python 3.12. The requirements-file install path and the pyproject/uv path can consequently behave differently.

**Remediation:** Choose and document one supported Python version for development, CI and hosting. Set `TIME_ZONE='Asia/Kolkata'` if business-facing timestamps should be India-local, and test timezone-aware order dates.

---

## 3. Positive controls already present

These controls are worth preserving while fixing the issues above:

- Django CSRF middleware is enabled in `main/main/settings.py`.
- Custom admin routes use login checks and superuser restrictions.
- Product deletion and several state-changing admin endpoints require POST.
- Product image uploads enforce a 5 MB limit, verify image data with Pillow, restrict formats to JPEG/PNG/WebP, and use the Cloudinary server API.
- Product and order prices use decimal fields; order price is derived from the current database product price and saved as a purchase-time total.
- Checkout rejects invalid quantity bounds and unavailable products.
- Saved-address mutations are scoped to `request.user.saved_addresses`.
- Existing tests already cover a number of pricing, availability, admin-access and address-ownership cases.

Those controls reduce risk but do not offset the public dump or anonymous order-enumeration issue.

---

## 4. Prioritized remediation plan

### Immediate — before any further promotion

1. **Handle `main/data.json` as an exposure incident:** remove it, purge it from repository history, rotate credentials/reset admin password, invalidate sessions, assess exposed customer data.
2. **Remove anonymous phone-substring order lookup.** Add ownership-based access and/or a secure guest-order token/OTP flow.
3. Pause public ordering if the exposed order records appear to match the deployed data until access is restricted and the issue is evaluated.

### Before accepting real customer orders

4. Fix multi-item checkout loss or disable multi-item cart checkout until server-side order lines exist.
5. Remove simulated live tracking and hard-coded delivery countdowns; render actual status.
6. Configure the splash screen with the real production backend URL, finite retries, visible fallback, correct asset path and tests.
7. Verify all food-safety, certification, sourcing, temperature, delivery-time, address and contact claims; remove unsupported claims.
8. Make production Django settings fail closed, use exact allowed hosts, and run deployment checks.
9. Upgrade Django to the latest compatible security patch, currently 6.0.9 as of this report, then test.
10. Whitelist payment/cut/slot values and independently validate delivery-address components on the server.
11. Prevent duplicate submissions with server-side idempotency/POST-Redirect-GET.

### Engineering/UX hardening

12. Replace cart `innerHTML` interpolation with safe DOM rendering.
13. Compile Tailwind CSS at build time and remove unnecessary external/runtime assets.
14. Correct dashboard metrics, timezone, brand spelling, support links, location and alt text.
15. Gate deployments on tests/scans, pin Actions to full SHAs, and protect `main`.
16. Remove the committed virtual environment and generated artifacts where safe.

---

## 5. Required regression test plan

### Privacy/access control

- Anonymous `GET /orders/?mobile=...` must never list orders.
- Test partial digits, letters, whitespace, phone prefixes and empty strings.
- A signed-in customer sees only their own orders.
- An order access token (if guest tracking is retained) must be unguessable, revocable/expiring and rate-limited.
- Customer A cannot view/edit Customer B’s address or order.

### Cart and checkout

- Two different products in the basket both appear in the saved order.
- Final amount is recomputed from database prices; tampering with `localStorage` price/total never changes the payable amount.
- Empty, invalid, unavailable and over-limit cart quantities are rejected server-side.
- Missing house/street/area/PIN information is rejected independently of JavaScript.
- A repeated checkout request does not create duplicate orders.
- Only permitted payment-method/slot/cut values are persisted.

### Status and customer messaging

- A `pending` order does not display as confirmed/preparing/on the way.
- Status timeline follows saved status transitions.
- ETA is displayed only when supported by actual order data/policy.
- WhatsApp links use the configured, verified shop number and correctly encode the message.

### Splash/deployment

- Production build with missing `VITE_API_BASE_URL` fails clearly or renders a recovery option—never loops against localhost.
- Backend unavailable, timeout, CORS error, invalid health payload and DB-not-ready states are handled.
- CSS/JS/fonts/images load with expected production headers.
- `DEBUG=False`, exact `ALLOWED_HOSTS`, CSRF, HTTPS and static storage work in the real deployment environment.

### Security/UI

- No live database exports, secret files, keys or virtual-environment binaries are tracked.
- Malformed localStorage entries and product names containing HTML cannot inject markup into the DOM.
- All buttons/links work, mobile pages have no horizontal overflow, forms have labels/errors, and reduced-motion is respected.
- No fake reviews, certifications, metrics or tracking states remain.

---

## 6. Scope and limitations

This report is based on static source inspection of the public GitHub `main` branch at commit `810267aa3d4991e301e7a56bbfa7f344c24bbd7a`. It did not include authenticated live testing, external scanning, payment-provider testing, Render/AWS configuration access, production database access, browser/device automation or an independent food-safety/legal verification. The production URL could not be fetched by the available web inspection mechanism during this review.

Therefore:

- Findings described as confirmed are confirmed in the checked source/configuration.
- Actual exploitability/reachability on the specific deployed hostname must still be verified after containment.
- Unsupported marketing claims are identified because they lack substantiation in this repository, not because this review independently disproved each claim.
- A clean test run or code change alone is not proof of production safety; retest the deployed system after remediation.

## 7. References

- [Repository main branch](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/tree/main)
- [Order lookup implementation](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/orders/views.py#L154-L172)
- [Public database-style export](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/data.json)
- [Cart rendering and checkout redirect](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/base/base.html#L490-L670)
- [Order confirmation UI](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/main/main/templates/orders/order_confirmation.html#L30-L110)
- [Splash screen health-check logic](https://github.com/Balarithik/Online-Ecommerce-Butcher-Shop/blob/main/SplashScreen/src/App.jsx#L1-L100)
- [Django 6.0.9 release notes](https://docs.djangoproject.com/en/dev/releases/6.0.9/)
- [Django security releases](https://docs.djangoproject.com/en/6.0/releases/security/)
- [OWASP Top 10:2025](https://top10.owasp.org/2025/)
- [GitHub Actions secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
