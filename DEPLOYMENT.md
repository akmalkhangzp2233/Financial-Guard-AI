# Deployment Guide

Three ways to deploy FinGuard AI, from fastest-for-a-demo to most "real":

| Path | Best for | Time |
|---|---|---|
| 1. Docker Compose (local) | Viva/demo on your own laptop, no internet needed | 5 min |
| 2. Render + Vercel (split hosting) | A live public URL to show examiners | 20 min |
| 3. Single Docker host (VPS) | Full control, one server | 30 min |

Pick ONE. Path 1 is enough for most final-year-project demos; do Path 2 only if
your evaluators specifically want a live link.

---

## Path 1 — Docker Compose (local, fastest)

Requirements: Docker Desktop installed.

```bash
git clone <your-repo-url> && cd FinGuard-AI
cp backend/.env.example backend/.env      # edit JWT_SECRET before real use
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend + Swagger docs: http://localhost:8000/docs
- Data persists in a Docker volume between restarts (`docker compose down` keeps
  it; `docker compose down -v` wipes it)
- ML models are already trained and shipped in `ml/models/*.pkl` — nothing to
  train before the demo

To stop: `docker compose down`

---

## Path 2 — Render (backend) + Vercel (frontend)

This is the standard "one service per platform" split for a FastAPI + React
app, and it's free on both platforms' hobby tiers.

### 2a. Backend on Render

1. Push this repo to GitHub.
2. In Render: **New +** → **Blueprint** → connect the repo → Render reads
   `render.yaml` automatically and provisions the web service + a free
   Postgres database.
3. Render generates `JWT_SECRET` for you (see `render.yaml`) and wires
   `DATABASE_URL` to the Postgres instance automatically.
4. Set `OPENAI_API_KEY` manually in the Render dashboard if you want real GPT
   tips (optional — the app works without it).
5. Once deployed, copy the backend's URL, e.g. `https://finguard-backend.onrender.com`.

**Free-tier note:** Render's free web services spin down after 15 minutes of
inactivity and take ~30-60s to wake on the next request. For a live demo,
open the URL a minute before your presentation starts to "warm" it.

### 2b. Frontend on Vercel

1. In Vercel: **Add New** → **Project** → import the same repo → set
   **Root Directory** to `frontend`.
2. Add an environment variable: `VITE_API_URL` = your Render backend URL from
   step 2a.5 (no trailing slash).
3. Deploy. `frontend/vercel.json` already handles the SPA routing fallback
   (fixes "404 on refresh at /budgets").
4. Go back to Render and update `CORS_ORIGINS` to include your new Vercel URL,
   then redeploy the backend.

---

## Path 3 — Single VPS with Docker Compose

Same as Path 1, but on a cloud VM (DigitalOcean/AWS Lightsail/etc):

```bash
ssh your-vps
git clone <your-repo-url> && cd FinGuard-AI
cp backend/.env.example backend/.env   # set a real JWT_SECRET
docker compose up -d --build
```

Then put nginx or Caddy in front for a real domain + free HTTPS (Caddy does
this with zero config — see https://caddyserver.com/docs/quick-starts/reverse-proxy).
`backend/main.py` already sends HSTS headers once `ENV=production`, so HTTPS
termination at the reverse proxy is all that's left.

---

## Environment variables reference

### `backend/.env`
| Variable | Required | Notes |
|---|---|---|
| `ENV` | recommended | `production` enables the JWT-secret safety check + HSTS header |
| `JWT_SECRET` | **yes in production** | generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | no | defaults to local SQLite; use Postgres for real deployment |
| `CORS_ORIGINS` | yes | comma-separated list of allowed frontend origins |
| `OPENAI_API_KEY` | no | enables real GPT tips; falls back to rule-based tips without it |
| `DEFAULT_RATE_LIMIT` | no | default `100/minute` per IP |

### `frontend/.env`
| Variable | Required | Notes |
|---|---|---|
| `VITE_API_URL` | yes | your backend's base URL, no trailing slash |

---

## Pre-deployment checklist

- [ ] `JWT_SECRET` is a real random value, not the default
- [ ] `.env` files are NOT committed (already covered by `.gitignore`)
- [ ] `CORS_ORIGINS` matches your actual frontend URL exactly (including `https://`)
- [ ] If demoing OCR: confirm the deploy target has `tesseract-ocr` installed —
      the provided Dockerfile handles this; a bare `pip install` on a fresh
      VM without Docker will NOT install the OS-level binary, so OCR will
      500 until you `apt-get install tesseract-ocr` manually
- [ ] Register your first account right after deploying — it's auto-promoted
      to admin (see `backend/routers/auth.py`)
