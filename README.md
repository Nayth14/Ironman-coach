# Ironman Coach

Web app + FastAPI coaching engine for personalized Ironman training.

## Architecture

```
web/              React SPA (Vite + Tailwind) — Netlify
coaching-lab/
  engine/         Deterministic coaching logic (Python)
  api/            FastAPI REST + SSE — Render/Fly
supabase/
  migrations/     Postgres schema
packages/db/      Shared TypeScript types
```

- **Engine**: all training-load decisions live in `coaching-lab/engine/`
- **API**: thin wrapper; LLM for chat/summaries only
- **Persistence**: Supabase Postgres when configured; local SQLite fallback for dev

## Quick start (local)

### 1. API

```bash
cd coaching-lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY (optional for fixture demo)
uvicorn api.main:app --reload --port 8000
```

Health check: http://127.0.0.1:8000/api/health

### 2. Web

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to port 8000.

### 3. Try without chat

Landing → **See a sample week** loads a fixture persona and builds a plan instantly.

## Supabase setup

1. Create a Supabase project
2. Run migrations in `supabase/migrations/` via the SQL editor (or `./scripts/deploy-supabase.sh`)
3. Add to `coaching-lab/.env`:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

4. Add to `web/.env`:

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

Without Supabase URL + service key the API uses SQLite at `coaching-lab/data/ironman_coach.db`.
When `SUPABASE_JWT_SECRET` is unset, the API accepts dev Bearer tokens for local auth testing.

### Auth providers (Supabase dashboard)

1. **Authentication → URL configuration**: add redirect URLs  
   - `http://localhost:5173/auth/callback`  
   - `https://your-production-domain/auth/callback`
2. **Authentication → Providers**: enable Google and Facebook OAuth (configure client IDs in Google Cloud / Meta).
3. **Authentication → Email**: enable email/password; set password recovery redirect to `/reset-password`.
4. Copy **JWT Secret** from Project Settings → API into `SUPABASE_JWT_SECRET`.

## Deployment

| Component | Host | Config |
|-----------|------|--------|
| SPA | Netlify | `netlify.toml` |
| API | Render | `render.yaml` + `coaching-lab/Dockerfile` |
| DB | Supabase | migrations in `supabase/migrations/` |

Set `VITE_API_URL` in Netlify to your Render API URL (or use the proxy redirect in `netlify.toml`).

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/guests` | Create guest profile |
| POST | `/api/chat/onboarding` | Onboarding chat (SSE) |
| POST | `/api/plans/generate` | Extract profile + build plan |
| POST | `/api/plans/{id}/activate` | Start week 1 |
| GET | `/api/plans/current` | Active plan + workouts |
| GET | `/api/workouts` | List workouts |
| PATCH | `/api/workouts/{id}/complete` | Log completion |
| POST | `/api/adaptations/evaluate` | Run adaptation engine |
| POST | `/api/chat/coaching` | Dashboard coach chat (SSE) |

All authenticated routes require `X-Guest-Id` header (stored in browser localStorage).

## Design

UI built to mockups in `.cursor/projects/.../assets/ironman-coach-*-mockup-v2.jpg`.

Design tokens: bg `#FAFAF8`, primary `#FF5436`, discipline colors for swim/bike/run/strength.
