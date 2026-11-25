# Kanban Board for Game Development

A self-hosted, single-container Kanban board for game-development workflows, built with FastAPI, SQLAlchemy, HTMX, and Jinja2. Runs on SQLite, no frontend build step, no database server.

## Status

Built in slices, one at a time (see `SPEC.md` for the full design):

| Slice | Scope | State |
|-------|-------|-------|
| 1 | Bootstrap | ✅ Done |
| 2 | Database & migrations | ✅ Done |
| 3 | Auth | ✅ Done |
| 4 | Projects | ✅ Done |
| 5 | Columns | ✅ Done |
| 6 | Cards | ✅ Done |

## Tech Stack (pinned)

- Python 3.12, FastAPI 0.115.12, SQLAlchemy 2.0.36, Alembic 1.14.0, Jinja2 3.1.6, HTMX 2.0.4, SortableJS 1.15.6, Argon2 23.1.0, pytest 8.3.4, Ruff 0.8.4
- Single Docker container, SQLite database file, server-rendered pages + HTMX/Alpine/SortableJS for interactivity.

## Quick Start

```bash
cp .env.example .env
docker compose up -d --build
```

Then open <http://localhost:8000>.

- Health check: <http://localhost:8000/healthz>

## Common Commands

```bash
docker compose logs -f web
docker compose exec web alembic upgrade head
docker compose exec web alembic revision --autogenerate -m "msg"
docker compose exec web pytest
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

## Development Rules (from `SPEC.md`)

- Work on one slice at a time.
- Don't change the schema, add dependencies, or change versions without approval.
- Services never import FastAPI/requests/templates; routes handle HTTP and templates.

## License

Local project — see repository owner for licensing.
