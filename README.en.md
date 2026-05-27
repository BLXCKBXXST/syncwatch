# Syncwatch

[Русский](README.md)

Self-hosted video platform with **synchronized watch rooms** — upload, browse,
watch alone, or pull friends into a room where everyone's player stays in sync.

![License](https://img.shields.io/badge/License-MIT-yellow)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5-092E20?logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

## Screenshots

| Feed | Watch | Room |
|------|-------|------|
| ![Feed](docs/screenshots/home.png) | ![Watch](docs/screenshots/watch.png) | ![Room](docs/screenshots/room.png) |

## Features

- Upload videos, browse a global feed, paginated.
- Per-video page with HLS-capable player and HTTP Range streaming (scrub & seek).
- **Synchronized rooms**: host controls playback, viewer players track the
  server clock with drift correction, invite-link join, guest access.
- Live chat with per-message likes; Q&A tab with up-votes.
- Passwordless auth via one-time email codes; JWT sessions.
- Three bundled UI themes (dark default, retro, light deep-blue) with an
  admin-set per-site default; per-user preference saved in `localStorage`.

## Tech stack

| Layer       | Stack                                                              |
|-------------|--------------------------------------------------------------------|
| Backend     | Django 5, Django REST Framework, Channels (WebSocket), Daphne (ASGI) |
| Real-time   | Redis channel layer                                                |
| Database    | PostgreSQL (prod), SQLite (local dev)                              |
| Auth        | JWT (djangorestframework-simplejwt) + one-time email codes         |
| Frontend    | React 19, React Router, Vite, axios, hls.js                        |
| Infra       | Docker Compose, nginx (frontend), Caddy (TLS at the edge)          |

## Quick start

```bash
docker compose up --build
# → http://localhost:8080
```

The bundled stack provisions PostgreSQL, Redis, the Django backend and the
React frontend, and exposes the app on port `8080`.

## Local development

Native, without Docker — useful for iterating on the frontend or running tests.

```bash
# Backend (SQLite, in-memory channel layer)
cd app/backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

```bash
# Frontend (separate terminal)
cd app/frontend
npm install
npm run dev
# → http://localhost:5173
```

Sign-in codes are printed to the backend log (console email backend).

## Project structure

```
syncwatch/
├── app/
│   ├── backend/        # Django apps: accounts, videos, rooms, chat, catalog, common
│   └── frontend/       # React + Vite
├── docker-compose.yml  # Self-contained stack
├── deploy.sh           # Idempotent server install (behind Caddy)
├── .env.example        # Environment variables template
└── API.md              # REST + WebSocket API reference
```

## Configuration

Copy `.env.example` to `.env` and edit. Without an `.env` file the stack runs on
SQLite + an in-memory channel layer — no external services required for local
development.

## Tests

```bash
# Backend
cd app/backend && .venv/bin/python -m pytest

# Frontend
cd app/frontend && npm run test
```

## License

[MIT](LICENSE).
