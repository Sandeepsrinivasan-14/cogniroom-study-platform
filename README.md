# CogniRoom — Collaborative Study Room

A real-time online study space with chat, a shared whiteboard, flashcards, quizzes,
a session scheduler, webcam-based "cognitive load" tracking, and an ML/LLM-powered
study assistant.

Built around **UN SDG 4** (Quality Education) and **SDG 8** (Decent Work &
Economic Growth): inclusive, lifelong learning tools that help groups study
effectively together.

---

## Tech stack

| Layer      | Details |
|------------|---------|
| Backend    | FastAPI, Socket.IO (ASGI), SQLAlchemy 2, Pydantic 2, python-jose (JWT), bcrypt |
| Realtime   | `python-socketio` — chat, whiteboard strokes, presence, live cognitive-load |
| Database   | SQLite for local dev, PostgreSQL in Docker |
| Cache      | Redis (optional) for live room metrics; in-memory fallback if absent |
| ML         | scikit-learn models for burnout risk, performance grade, and engagement score |
| LLM agents | Ollama (local) with a hardcoded fallback; optional OpenAI-compatible endpoint for quiz generation |
| Frontend   | React 19 + Vite, React Router, Recharts, Framer Motion, `socket.io-client` |

---

## Project structure

```
.
├── src/                     # FastAPI application
│   ├── main.py              # app, routes, Socket.IO events
│   ├── auth.py              # JWT + bcrypt (legacy SHA-256 verified & auto-upgraded)
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # engine / session
│   ├── analytics_service.py # user & room analytics (ML-backed, heuristic fallback)
│   ├── agents_service.py    # multi-agent LLM advisor with model failover
│   ├── live_metrics.py      # Redis-backed live cognitive-load metrics
│   ├── redis_service.py     # Redis wrapper (degrades gracefully)
│   ├── routes/              # load, schedule, whiteboard, audio, agent routers
│   ├── ml/                  # ML service + training scripts + committed models
│   └── templates/           # /dev developer dashboard
├── frontend/                # React + Vite client
├── ml/                      # engagement model + feature export
├── scripts/migrate.py       # Postgres column migrations
├── tests/harsh_test.py      # end-to-end API smoke test (needs a running server)
├── docker-compose.yml       # backend + Postgres + Redis
└── Dockerfile
```

---

## Getting started

### 1. Configuration

```bash
cp .env.example .env
# generate a key and paste it into .env as SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`SECRET_KEY` is **required**. With `DEBUG=true` a random ephemeral key is used if
it is unset (tokens reset on restart); otherwise the app refuses to start.

### 2. Backend (local, SQLite)

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn src.main:app --reload
```

API: <http://localhost:8000>  ·  Docs: <http://localhost:8000/docs>  ·
Dev dashboard: <http://localhost:8000/dev>

### 3. Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

The client talks to `http://localhost:8000` (see `frontend/src/api/client.js`).

### 4. Everything in Docker

```bash
docker compose up --build
```

Starts the backend (`:8000`), PostgreSQL (`:5433`), and Redis (`:6379`).
`SECRET_KEY` is read from `.env`.

---

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `SECRET_KEY` | yes | JWT signing key |
| `DATABASE_URL` | no | defaults to `sqlite:///./studyroom.db` |
| `DEBUG` | no | `true` enables the ephemeral-key dev fallback |
| `REDIS_URL` | no | live metrics; falls back to no-op without it |
| `OLLAMA_URL`, `OLLAMA_PRIMARY_MODEL`, `OLLAMA_FALLBACK_MODEL` | no | local LLM advisor |
| `LLM_BASE_URL`, `LLM_API_KEY` | no | OpenAI-compatible endpoint for `/llm/quiz/generate` (returns `503` until both are set) |

---

## Machine learning

Three scikit-learn models are trained on synthetic session data and **committed**
under `src/ml/` and `ml/`:

| Model | Task | Script |
|-------|------|--------|
| `burnout_model_balanced.pkl` | burnout risk (low/medium/high) | `python -m src.ml.train_burnout_balanced` |
| `performance_model_balanced.pkl` | projected grade (A–D) | `python -m src.ml.train_performance_balanced` |
| `ml/engagement_model.pkl` | engagement score (0–1) | `python src/train_engagement_model.py` |

Models are validated with a self-test at load time; if a pickle is incompatible
with the installed `numpy` / `scikit-learn` the service transparently falls back
to heuristics and reports `prediction_source: "heuristic"`. **Retrain and
re-commit the models whenever those pinned versions change.**

---

## API overview

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /me` |
| Rooms | `POST /rooms`, `POST /rooms/join/{code}`, `GET /rooms/my`, `GET /rooms/{id}/events` |
| Quizzes | `POST /rooms/{id}/quizzes`, `GET /rooms/{id}/quizzes`, `POST /quizzes/{id}/attempts`, `GET /rooms/{id}/stats/quiz` |
| Flashcards | `POST /rooms/{id}/flashcards/decks`, `GET /rooms/{id}/flashcards/decks`, `GET /flashcards/decks/{id}` |
| Scheduler | `POST/GET /rooms/{id}/schedule/`, `DELETE /rooms/{id}/schedule/{item_id}` |
| Analytics | `GET /users/me/analytics`, `GET /rooms/{id}/analytics`, `GET /analytics/room/{id}/activity` |
| AI | `GET /users/me/agent/suggestions`, `GET /rooms/{id}/agent/suggestions`, `POST /llm/quiz/generate` |
| Realtime | `ws://localhost:8000/socket.io` — `chatmessage`, `whiteboard_update`, `presence_update`, `webcam_load_update`, `quiz_start`, `quiz_answer` |

Full interactive reference at `/docs`.

---

## Tests

```bash
uvicorn src.main:app &          # start the server first
python tests/harsh_test.py      # end-to-end happy-path smoke test
```

---

## License

Educational project.
