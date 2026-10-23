# SplashScreen (React + Vite)

Warm-up / branding screen shown before customers enter the Django storefront. It polls the Django **`/healthz/`** endpoint, then redirects to `VITE_API_BASE_URL` when the backend is ready (with a capped retry count so it does not loop forever).

## Tech stack

| Piece | Version / tool |
|-------|----------------|
| UI | React 19 |
| Build | Vite 8 |
| Lint | Oxlint |
| Language | JavaScript (JSX) |

## Setup

```bash
npm install
```

Create `SplashScreen/.env` (gitignored):

```dotenv
VITE_API_BASE_URL=https://lakshmi-broliers.onrender.com
```

Local Django example: `VITE_API_BASE_URL=http://127.0.0.1:8000`

`VITE_API_BASE_URL` is **required** — the app throws at startup if it is missing.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | Production build → `dist/` |
| `npm run preview` | Preview the production build |
| `npm run lint` | Oxlint |

## File map

| Path | Purpose |
|------|---------|
| `package.json` / `package-lock.json` | npm deps and scripts. |
| `vite.config.js` | Vite + React plugin config. |
| `index.html` | HTML shell Vite injects the React bundle into. |
| `.oxlintrc.json` | Oxlint rules. |
| `.gitignore` | Ignores `node_modules/`, `dist/`, `.env`. |
| `.env` | Local `VITE_API_BASE_URL` (not committed). |
| `public/favicon.svg` | Tab icon. |
| `public/icons.svg` | Static SVG sprite/icons for the splash UI. |
| `src/main.jsx` | React root mount. |
| `src/App.jsx` | Splash UI, health-check polling (`MAX_RETRIES=10`), redirect logic. |
| `src/App.css` / `src/index.css` | Splash styling. |
| `src/assets/logo.png` | Brand mark on the splash. |
| `src/assets/logo_aramcuts.png` | Alternate brand asset. |
| `src/assets/hero.png` | Hero imagery. |
| `src/assets/react.svg` / `vite.svg` | Template leftovers (optional). |
| `dist/` | Built static site from `npm run build` (deploy separately if used as a static host). |

## Workflow with Django

1. Start Django (`main/` → `runserver` or production Gunicorn).
2. Confirm `GET {VITE_API_BASE_URL}/healthz/` returns `{"status":"ok"}`.
3. Run or deploy this splash; it redirects users into the store when healthy.
4. After 10 failed health checks it stops retrying and shows an error/ready state instead of hammering localhost or the API forever.
