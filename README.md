# Finance Tracking API

FastAPI backend: income/expense **CRUD**, **filters**, **summaries** (totals, category breakdown, monthly), **roles** (viewer / analyst / admin), optional **JWT auth**, **SQLite** or **PostgreSQL**.

## Live (Render)

| | URL |
|--|-----|
| **API (root)** | [https://finance-tracking-api.onrender.com](https://finance-tracking-api.onrender.com) |
| **Swagger / OpenAPI docs** | [https://finance-tracking-api.onrender.com/docs](https://finance-tracking-api.onrender.com/docs) |
| **Health** | [https://finance-tracking-api.onrender.com/health](https://finance-tracking-api.onrender.com/health) |

**GitHub:** [Yashi1211/finance-tracking-api](https://github.com/Yashi1211/finance-tracking-api)

## Quick start (local)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Docs:** http://127.0.0.1:8000/docs  
- **JSON root:** http://127.0.0.1:8000/  
- After building the UI: http://127.0.0.1:8000/ui/

Copy `.env.example` to `.env` to override `DATABASE_URL` or `SECRET_KEY`.

## Deploy on Render (free live URL)

Render par login **tumhari** ID se karna hoga. Repo mein `render.yaml` hai taaki setup fast ho.

1. Code push ho chuka ho: [GitHub repo](https://github.com/Yashi1211/finance-tracking-api) (ya apna fork).
2. [dashboard.render.com](https://dashboard.render.com) → sign up / log in (GitHub se connect).
3. **New +** → **Blueprint** → Connect repository → `Yashi1211/finance-tracking-api` chuno → branch **main**.
4. Render `render.yaml` read karega → **Apply** / **Create resources**.
5. Is repo ke current deploy ke URLs:
   - **API:** https://finance-tracking-api.onrender.com  
   - **Swagger:** https://finance-tracking-api.onrender.com/docs  
   - **Health:** https://finance-tracking-api.onrender.com/health  
   (Agar apna service naam alag rakha ho to Render dashboard se exact URL copy karna.)

**Note (free tier):** service ~15 min idle ke baad sleep ho sakti hai; pehli request 30–60 sec slow ho sakti hai. SQLite file deploy/restart par reset ho sakti hai — demo ke liye OK; production ke liye Render PostgreSQL + `DATABASE_URL` add karo.

## Auth

1. **JWT (recommended)**  
   - `POST /auth/register` — body: `username`, `password`, `role` (`viewer` | `analyst` | `admin`)  
   - `POST /auth/login` — body: `username`, `password` → `access_token`  
   - Send `Authorization: Bearer <token>` on other routes.

2. **Dev fallback**  
   - Header `X-Role: viewer|analyst|admin`  
   - If neither JWT nor `X-Role`, role defaults to **admin** (local demo only).

## Roles

| Role     | Can do |
|----------|--------|
| viewer   | List/get transactions **without** query filters; `GET /summary/viewer` |
| analyst  | Filters on `GET /transactions`; full `GET /summary` |
| admin    | Create/update/delete transactions + analyst abilities |

## Main endpoints

| Method | Path | Notes |
|--------|------|--------|
| GET | `/transactions` | Paginated: `{ items, total, skip, limit }` |
| POST | `/transactions` | Admin |
| GET | `/transactions/{id}` | |
| PATCH | `/transactions/{id}` | Admin |
| DELETE | `/transactions/{id}` | Admin |
| GET | `/summary/viewer` | Totals only |
| GET | `/summary` | Analyst+; query filters like list |

Query filters (analyst/admin): `date_from`, `date_to`, `category`, `type`.

## Tests

```bash
python -m pytest tests/ -v
```

## Docker (API + PostgreSQL)

```bash
docker compose up --build
```

API: http://127.0.0.1:8000  

## Web UI (optional)

```bash
cd frontend
npm install
npm run dev          # dev: http://127.0.0.1:5173 — calls API on :8000
npm run build        # output: frontend/dist — served by FastAPI at /ui/
```

Restart `uvicorn` after `npm run build` so `/ui/` is mounted.

## Example `curl`

Replace `BASE` with `http://127.0.0.1:8000` (local) or `https://finance-tracking-api.onrender.com` (live).

```bash
BASE=http://127.0.0.1:8000

# Register + login
curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" -d "{\"username\":\"me\",\"password\":\"secret12\",\"role\":\"admin\"}"
curl -s -X POST "$BASE/auth/login" -H "Content-Type: application/json" -d "{\"username\":\"me\",\"password\":\"secret12\"}"

# Create transaction (replace TOKEN)
curl -s -X POST "$BASE/transactions" -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d "{\"amount\":500,\"type\":\"expense\",\"category\":\"Food\",\"date\":\"2026-04-01\",\"note\":\"Pizza\"}"
```
