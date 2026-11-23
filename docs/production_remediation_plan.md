# Production Remediation Plan — Lakshmi Broliers

Based on the [full audit report](Lakshmi_Broilers_Security_UI_Production_Audit.md), status of remediation work.

---

## Already fixed (prior work)

| # | Issue | Status |
|---|-------|--------|
| P0-2 | Anonymous phone-substring order lookup | Done — `my_orders` requires login, filters by `user=request.user` |
| P1-1 | Cart sends only first item to checkout | Done — server-side `Cart` / `CartItem` / `OrderItem` |
| P1-2 | Fake live tracking on order confirmation | Done — renders actual `order.status` |
| P2-3 | Address not validated server-side | Done — `OrderForm.clean_address()` |
| P2-4 | Duplicate order submissions | Done — `placement_token` + idempotency |
| P1-5 | `DEBUG=True` default in production | Done — `SECRET_KEY` required when `DEBUG=False`; secure cookies |
| — | Login required for ordering | Done — Checkout / Orders require auth |
| P2-1 | Unsafe HTML in client cart | Done — `textContent` / `createElement` |
| P1-3 | Splash retries forever / localhost | Done — no localhost fallback; `MAX_RETRIES=10` |
| P3-1 | `.venv` tracked in git | Done — gitignored / untracked |
| P3-2 | `TIME_ZONE='UTC'` | Done — `Asia/Kolkata` |

---

## All remediation items complete

### Phase 1: Critical security
- **P0-1**: `data.json` removed, gitignored, purged from history
- **P1-6**: Django upgraded to **6.0.9**
- **CSRF signup/login (Oct 2026)**: Production `403 CSRF token from POST incorrect` on `/signup/` — fixed with `@never_cache` + `@ensure_csrf_cookie` on customer auth (same pattern as admin login), `CSRF_FAILURE_VIEW`, explicit `CSRF_TRUSTED_ORIGINS` / SameSite settings, and client-side CSRF field sync in `base.html` for mobile bfcache

### Phase 2: Business logic & validation
- **P2-2**: Payment/cut/slot via `ChoiceField` in `OrderForm`
- **P2-5**: Admin metrics: `delivered_revenue` vs `total_order_value`
- **P2-1** / **P1-3**: As above

### Phase 3: Content & claims
- **P1-4**: Removed unsubstantiated marketing claims
- **P2-7**: Standardized `WHATSAPP_NUMBER`; About page address / hygiene copy cleaned up

### Phase 4: DevOps & hardening
- **P2-6**: Tailwind CDN acceptable for MVP
- **P3-1** / **P3-2**: As above
- READMEs updated for current stack, workflows, and per-file purpose maps

### Phase 5: UI cleanup
- Removed fake urgency / excessive animation / unverified About claims
- `my_orders` requires login

---

## Verification checklist (CSRF)

1. Open `/signup/` (incognito), create account → expect redirect, not 403.
2. Confirm response headers on GET `/signup/` include `Cache-Control: … no-store …`.
3. Regression: `python manage.py test home.tests.CustomerAuthenticationTests`
