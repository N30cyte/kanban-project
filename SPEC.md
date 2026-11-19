# Kanban Board for Game Development – Design Specification
**Project:** `kanban-project`
**Author:** Jacob
**Date:** 2026-11-16

---

## 1. Overview

This project is a self-hosted web application, running in a single Docker container on a local machine, that provides a Kanban board tailored for game-development workflows. It supports:

- **Projects** – a separate board per game or sprint.
- **Workflow columns** – user-defined stages plus a mandatory *Complete* column.
- **Cards & Subtasks** – Markdown-enabled tickets with MoSCoW priority tags.
- **Future views** – a flowchart planner and a vision/inspiration board that reference the same cards.
- **Auth** – simple email/password login (OAuth stub for future Google login).

The goal is to ship a minimal, functional MVP with clean, simple code that a local AI model can reliably help build and maintain.

### Guiding principle
Fewest moving parts. One language (Python) for all application logic, one container, one database file, no frontend build step. JavaScript is limited to small, vendored libraries for interactivity (drag and drop, modals).

---

## 2. Tech Stack & Pinned Versions

All versions are pinned exactly. Do not upgrade or substitute any of them without approval (see §10).

### 2.1 Runtime & Container

| Layer | Technology | Pinned version | Docs |
|-------|------------|----------------|------|
| Language | Python | 3.12 | https://docs.python.org/3.12/ |
| Base image | `python:3.12-slim-bookworm` | 3.12 (slim, Debian Bookworm) | https://hub.docker.com/_/python |
| Containers | Docker Compose (Compose Specification, no `version:` key) | Bundled with Docker Desktop | https://docs.docker.com/compose/ · File reference: https://docs.docker.com/reference/compose-file/ |
| Database | SQLite (bundled with Python's `sqlite3`) | Bundled with Python 3.12 | https://www.sqlite.org/docs.html · Python module: https://docs.python.org/3.12/library/sqlite3.html |

### 2.2 Python Packages (`requirements.txt`)

| Purpose | Package | Pinned version | Docs |
|---------|---------|----------------|------|
| Web framework | `fastapi` | 0.115.12 | https://fastapi.tiangolo.com/ · Release: https://github.com/fastapi/fastapi/releases/tag/0.115.12 |
| ASGI server | `uvicorn[standard]` | 0.34.0 | https://www.uvicorn.org/ · Release: https://github.com/encode/uvicorn/releases/tag/0.34.0 |
| Validation | `pydantic` | 2.10.6 | https://docs.pydantic.dev/2.10/ |
| ORM | `sqlalchemy` | 2.0.36 | https://docs.sqlalchemy.org/en/20/ · Changelog: https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html#change-2.0.36 |
| Migrations | `alembic` | 1.14.0 | https://alembic.sqlalchemy.org/en/latest/ · Changelog: https://alembic.sqlalchemy.org/en/latest/changelog.html#change-1.14.0 |
| Templates | `jinja2` | 3.1.6 | https://jinja.palletsprojects.com/en/3.1.x/ |
| Form parsing | `python-multipart` | 0.0.20 | https://github.com/Kludex/python-multipart · Release: https://github.com/Kludex/python-multipart/releases/tag/0.0.20 |
| Session signing | `itsdangerous` | 2.2.0 | https://itsdangerous.palletsprojects.com/en/2.2.x/ |
| Password hashing | `argon2-cffi` | 23.1.0 | https://argon2-cffi.readthedocs.io/en/23.1.0/ |
| Markdown rendering | `markdown-it-py` | 3.0.0 | https://markdown-it-py.readthedocs.io/en/latest/ · Release: https://github.com/executablebooks/markdown-it-py/releases/tag/v3.0.0 |
| Testing | `pytest` | 8.3.4 | https://docs.pytest.org/en/8.3.x/ |
| Test client | `httpx` (used by FastAPI's `TestClient`) | 0.28.1 | https://www.python-httpx.org/ · Release: https://github.com/encode/httpx/releases/tag/0.28.1 |
| Lint & format | `ruff` | 0.8.4 | https://docs.astral.sh/ruff/ · Release: https://github.com/astral-sh/ruff/releases/tag/0.8.4 |

Note: FastAPI and Ruff do not publish per-version docs; their main docs describe the latest release, so use the linked release notes to check what applies to the pinned version.

```text
# requirements.txt
fastapi==0.115.12
uvicorn[standard]==0.34.0
pydantic==2.10.6
sqlalchemy==2.0.36
alembic==1.14.0
jinja2==3.1.6
python-multipart==0.0.20
itsdangerous==2.2.0
argon2-cffi==23.1.0
markdown-it-py==3.0.0

# dev / test (kept in the same file: local-only app, one image)
pytest==8.3.4
httpx==0.28.1
ruff==0.8.4
```

The Docker image installs from `requirements.lock` — the full resolved set (including transitive packages such as Starlette) captured once via `pip freeze` from a `python:3.12-slim-bookworm` container after installing `requirements.txt`. Locking the transitive set ensures builds never re-resolve versions (unlocked resolution caused past build failures). When `requirements.txt` changes, regenerate the lock the same way.

### 2.3 Frontend Libraries (vendored, no build step)

These files are downloaded once into `app/static/vendor/` and committed. Pages load them from there, never from a CDN, so the app works offline and versions cannot drift.

| Purpose | Library | Pinned version | Docs | Vendored file source |
|---------|---------|----------------|------|----------------------|
| Server interactions | HTMX | 2.0.4 | https://htmx.org/docs/ (v2 docs; v1 docs live at v1.htmx.org and must not be used) · Release: https://github.com/bigskysoftware/htmx/releases/tag/v2.0.4 | https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js |
| Small UI state (modals, dropdowns) | Alpine.js | 3.14.1 | https://alpinejs.dev/ · Release: https://github.com/alpinejs/alpine/releases/tag/v3.14.1 | https://unpkg.com/alpinejs@3.14.1/dist/cdn.min.js |
| Drag and drop | SortableJS | 1.15.6 | https://github.com/SortableJS/Sortable/tree/1.15.6 (README is the docs) | https://unpkg.com/sortablejs@1.15.6/Sortable.min.js |
| Styling | Hand-written CSS with custom properties | – | https://developer.mozilla.org/en-US/docs/Web/CSS | `app/static/css/app.css` |

### 2.4 Future-View Libraries (not installed yet)

Chosen and pinned at the start of the relevant slice, after approval. Candidates, all plain JavaScript and usable without a build step:

| View | Candidates | Docs |
|------|------------|------|
| Flowchart | Drawflow, Cytoscape.js | https://github.com/jerosoler/Drawflow · https://js.cytoscape.org/ |
| Vision board | Konva.js, Fabric.js | https://konvajs.org/docs/ · https://fabricjs.com/docs/ |

---

## 3. Data Model

SQLAlchemy 2.0 ORM (typed `Mapped[...]` / `mapped_column(...)` style). Primary keys are auto-incrementing integers. All tables have `created_at` and `updated_at` (UTC). Deletes cascade from parent to children.

### 3.1 Core Tables (MVP)

| Table | Fields | Notes |
|-------|--------|-------|
| **users** | `id` INTEGER PK, `email` TEXT UNIQUE NOT NULL, `password_hash` TEXT NOT NULL | Argon2 hash. |
| **projects** | `id` INTEGER PK, `user_id` FK → users.id, `name` TEXT NOT NULL | One board per project. |
| **columns** | `id` INTEGER PK, `project_id` FK → projects.id, `name` TEXT NOT NULL, `position` INTEGER NOT NULL, `is_complete` BOOLEAN NOT NULL DEFAULT false | Exactly one `is_complete` column per project. |
| **cards** | `id` INTEGER PK, `column_id` FK → columns.id, `title` TEXT NOT NULL, `description` TEXT (Markdown), `priority` priority (see 3.3) NOT NULL DEFAULT `needs_assigning`, `position` INTEGER NOT NULL | Order within its column. |
| **subtasks** | `id` INTEGER PK, `card_id` FK → cards.id, `title` TEXT NOT NULL, `description` TEXT, `priority` priority NOT NULL DEFAULT `needs_assigning`, `is_done` BOOLEAN NOT NULL DEFAULT false, `position` INTEGER NOT NULL | Order within its card. |

### 3.2 Future-View Tables (planned, not created until their slice)

Each view stores only its own layout. Card content always lives in `cards`, so one card can appear on the board, in a flowchart, and on the vision board without duplication.

| Table | Fields | Notes |
|-------|--------|-------|
| **flow_nodes** | `id`, `project_id` FK, `card_id` FK → cards.id NULL, `label` TEXT, `x` REAL, `y` REAL | `card_id` NULL means a free-standing node. |
| **flow_edges** | `id`, `project_id` FK, `from_node_id` FK → flow_nodes.id, `to_node_id` FK → flow_nodes.id, `label` TEXT NULL | Directed connection. |
| **board_items** | `id`, `project_id` FK, `card_id` FK → cards.id NULL, `kind` TEXT (`image`, `text`, `note`), `content` TEXT NULL, `image_path` TEXT NULL, `x`, `y`, `width`, `height` REAL, `z_index` INTEGER | Images stored as files under `data/uploads/`; only the path goes in the database. |

### 3.3 Priority Values

Stored as TEXT with a CHECK constraint (SQLAlchemy `Enum(..., native_enum=False)`), mapped to a Python `enum.Enum`:

```python
class Priority(str, enum.Enum):
    must_have = "must_have"
    should_have = "should_have"
    could_have = "could_have"
    wont_have = "wont_have"
    needs_assigning = "needs_assigning"
```

### 3.4 Business Rules

- Creating a project automatically creates its *Complete* column.
- The *Complete* column cannot be renamed or deleted.
- Positions are integers starting at 0. After any reorder or move, the affected list is renumbered 0..n-1 in a single transaction.
- Deleting a column requires it to be empty, or the user confirms and its cards are deleted with it.

### 3.5 SQLite Requirements (must be implemented)

SQLite does not enforce foreign keys unless asked, and cannot alter tables in place. Both are handled once, centrally:

```python
# app/db.py
from sqlalchemy import create_engine, event

def make_engine(url: str):
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine
```

In `migrations/env.py`, call `context.configure(..., render_as_batch=True)` so Alembic can apply column changes on SQLite.

---

## 4. Routes

The app is server-rendered. Page routes return full HTML pages; HTMX routes return HTML fragments that HTMX swaps into the page. JSON is used only for `/healthz`. Every route except `/healthz`, `/login`, and `/register` requires a logged-in user.

When an unauthenticated request arrives, normal requests get `303 → /login`; HTMX requests (header `HX-Request: true`) get `200` with header `HX-Redirect: /login`.

### 4.1 Pages & Auth

| Method | Path | Form fields | Response |
|--------|------|-------------|----------|
| GET | `/healthz` | – | 200 JSON `{"status": "ok"}` |
| GET | `/register` | – | Register page |
| POST | `/register` | `email`, `password` | 303 → `/login`; 400 page with error on invalid input; 409 if email exists |
| GET | `/login` | – | Login page |
| POST | `/login` | `email`, `password` | 303 → `/`; 401 page with error on bad credentials |
| POST | `/logout` | – | 303 → `/login` |
| GET | `/` | – | 303 → first project's board, or the empty "create a project" page |

### 4.2 Projects, Columns, Cards, Subtasks

| Method | Path | Form fields | Response |
|--------|------|-------------|----------|
| POST | `/projects` | `name` | 303 → `/projects/{id}` |
| GET | `/projects/{id}` | – | Board page (sidebar + columns + cards) |
| PATCH | `/projects/{id}` | `name` | Board header fragment |
| DELETE | `/projects/{id}` | – | `HX-Redirect: /` |
| POST | `/projects/{id}/columns` | `name` | New column fragment |
| POST | `/projects/{id}/columns/reorder` | `column_ids` (ordered, repeated field) | 204 |
| PATCH | `/columns/{id}` | `name` | Column header fragment; 400 if *Complete* |
| DELETE | `/columns/{id}` | – | 200 empty body (HTMX removes element); 400 if *Complete* |
| POST | `/columns/{id}/cards` | `title` | New card fragment |
| POST | `/cards/move` | `card_id`, `to_column_id`, `card_ids` (destination column's full order) | 204 |
| GET | `/cards/{id}` | – | Card detail modal fragment |
| PATCH | `/cards/{id}` | `title`, `description`, `priority` (any subset) | Updated card fragment |
| DELETE | `/cards/{id}` | – | 200 empty body |
| POST | `/cards/{id}/subtasks` | `title` | New subtask fragment |
| PATCH | `/subtasks/{id}` | `title`, `description`, `priority`, `is_done` (any subset) | Updated subtask fragment |
| DELETE | `/subtasks/{id}` | – | 200 empty body |
| POST | `/markdown/preview` | `text` | Rendered HTML fragment |

### 4.3 Future Views (stubs in MVP)

| Method | Path | Response |
|--------|------|----------|
| GET | `/projects/{id}/flowchart` | Placeholder page with view tabs |
| GET | `/projects/{id}/vision` | Placeholder page with view tabs |
| GET | `/auth/google` | 501 page: "Google login is not available yet" |

---

## 5. UI Description

### 5.1 Main Layout
```
+-------------------+-------------------------------------------------+
| Sidebar (240 px)  | Board Header: <Project Name> (click to edit)    |
| • Projects list   | View tabs: [Board] [Flowchart] [Vision Board]   |
| • + New Project   |                         [+ New Column] (right)  |
| • Log out         +-------------------------------------------------+
|                   | Columns (horizontal scroll, draggable)          |
|                   |  +----------------------+  +----------------+   |
|                   |  | <Column> (editable)  |  | Complete       |   |
|                   |  | ⋮⋮ drag handle       |  | (locked)       |   |
|                   |  +----------------------+  +----------------+   |
|                   |  | Card: title          |  | Card ...       |   |
|                   |  |   priority badge     |  |                |   |
|                   |  |   subtask count 2/5  |  |                |   |
|                   |  | + Add card           |  | + Add card     |   |
|                   |  +----------------------+  +----------------+   |
+-------------------+-------------------------------------------------+
```

- Cards drag within a column and across columns (SortableJS, shared group). On drop, the page posts to `/cards/move`.
- Columns drag by their handle. On drop, the page posts to `/projects/{id}/columns/reorder`.
- Clicking a card opens the detail modal (loaded with `GET /cards/{id}`; open/close state handled by Alpine.js).

### 5.2 Card Detail Modal (Split-View Markdown Editor)
```
+------------------------------------------------------------------+
| Card Title (editable)                  Priority: [MoSCoW ▼]      |
+-------------------------------+----------------------------------+
| Markdown Editor               | Live Preview (rendered)          |
| <textarea>                    |                                  |
+-------------------------------+----------------------------------+
| Subtasks                                                         |
|   [ ] Subtask 1   (editable title, priority badge)  [delete]     |
|   [x] Subtask 2                                     [delete]     |
|   + Add subtask                                                  |
+------------------------------------------------------------------+
| [Save]                                           [Delete Card]   |
+------------------------------------------------------------------+
```

- The preview updates as the user types: the textarea posts to `/markdown/preview` with `hx-trigger="input changed delay:300ms"`.
- Markdown is rendered on the server with `markdown-it-py` using `MarkdownIt("commonmark", {"html": False})`, so raw HTML in descriptions is never executed. The same function renders both the preview and saved descriptions.
- Priority badges use distinct colors per MoSCoW value, with the text label always visible.

### 5.3 Future Views
- **Flowchart view** – diagram editor whose nodes can link to cards (`flow_nodes.card_id`). Clicking a linked node opens the same card modal.
- **Vision board view** – free-form canvas of images, text, and notes, optionally linked to cards (`board_items.card_id`).

---

## 6. Project Structure & Conventions
```
kanban-project/
├─ app/
│  ├─ main.py            # create FastAPI app, middleware, mount static, include routers
│  ├─ config.py          # read settings from environment (.env)
│  ├─ db.py              # engine (make_engine), SessionLocal, Base, get_db dependency
│  ├─ models.py          # SQLAlchemy models + Priority enum
│  ├─ auth.py            # password hashing, current-user dependency
│  ├─ markdown.py        # render_markdown(text) -> safe HTML
│  ├─ routes/            # HTTP layer: parse form, call service, render template
│  │  ├─ auth.py
│  │  ├─ projects.py
│  │  ├─ columns.py
│  │  ├─ cards.py
│  │  └─ subtasks.py
│  ├─ services/          # database queries and business rules (no HTTP, no templates)
│  │  ├─ projects.py
│  │  ├─ columns.py
│  │  ├─ cards.py
│  │  └─ subtasks.py
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ login.html
│  │  ├─ register.html
│  │  ├─ board.html
│  │  └─ partials/       # column.html, card.html, card_modal.html, subtask.html, sidebar.html
│  └─ static/
│     ├─ css/app.css
│     ├─ js/board.js     # SortableJS setup only
│     └─ vendor/         # htmx.min.js, alpine.min.js, Sortable.min.js (pinned, committed)
├─ migrations/           # Alembic
├─ tests/
│  ├─ conftest.py
│  └─ test_*.py
├─ data/                 # SQLite file + uploads (Docker volume, git-ignored)
├─ alembic.ini
├─ requirements.txt
├─ requirements.lock
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
├─ .dockerignore
├─ .gitignore
├─ README.md
└─ SPEC.md
```

- **Naming** – `snake_case` for Python files, functions, and variables; `PascalCase` for classes; lowercase hyphenated CSS class names.
- **Layers** – routes never run queries directly; services never import FastAPI, Request, or templates.
- **File size** – keep each file under about 200 lines; split by feature when one grows past that.
- **Style** – `ruff check .` and `ruff format .` must be clean.
- **Types** – type hints on all function signatures.

---

## 7. Environment & Docker

### 7.1 `.env.example`
```env
SECRET_KEY=change-me-to-a-long-random-string
DATABASE_URL=sqlite:////app/data/kanban.db
```
Copy to `.env` (git-ignored). `SECRET_KEY` signs the session cookie.

### 7.2 `Dockerfile`
```dockerfile
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir --timeout 60 --retries 10 -r requirements.lock

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```
Note: Slice 1's CMD omits `alembic upgrade head &&` (no migrations exist yet); Slice 2 adds it when the initial migration lands. `--timeout 60 --retries 10` hardens the install against flaky networks (a mid-build download timeout once aborted the whole build).

### 7.3 `docker-compose.yml`
```yaml
services:
  web:
    build: .
    container_name: kanban-web
    restart: unless-stopped
    env_file: .env
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ./data:/app/data            # database + uploads persist here
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 15s
```
Code is baked into the image (dev loop: `docker compose up -d --build`); there are no code bind-mounts and no `--reload`, so nothing relies on host file watching. `data/` contains a committed `.gitkeep` so the mount target always exists.

### 7.4 `.dockerignore`
```text
data/
.env
.git/
__pycache__/
*.pyc
.DS_Store
.pytest_cache/
.ruff_cache/
```

### 7.5 Common Commands
```bash
docker compose up -d --build                                   # build and start
open http://localhost:8000                                     # use the app
docker compose logs -f web                                     # watch logs
docker compose exec web alembic revision --autogenerate -m "msg"  # new migration
docker compose exec web alembic upgrade head                   # apply migrations
docker compose exec web pytest                                 # run tests
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

### 7.6 Calling the Local Model From the App (optional, future)
LM Studio runs on the Mac host, not in the container. From inside the container, reach its OpenAI-compatible server at `http://host.docker.internal:1234/v1`.

---

## 8. Build Order

Each slice is built, tested, and committed before the next begins.

| # | Slice | Done when |
|---|-------|-----------|
| 1 | Bootstrap | `docker compose up` starts cleanly; `/healthz` returns `{"status": "ok"}`; `base.html` renders with HTMX, Alpine, and SortableJS loaded from `static/vendor/` (no console errors). |
| 2 | Database & migrations | Models for users, projects, columns, cards, subtasks; initial Alembic migration applies on startup; a test confirms foreign keys are enforced. |
| 3 | Auth | Register, login, logout work; protected pages redirect to `/login`; HTMX requests receive `HX-Redirect`. |
| 4 | Projects | Sidebar lists projects; create, rename, delete work; new projects get a locked *Complete* column. |
| 5 | Columns | Add, rename, delete, and drag-reorder columns; order persists after reload; *Complete* cannot be renamed or deleted. |
| 6 | Cards | Add cards; drag within and across columns; order persists after reload and after `docker compose restart`. |
| 7 | Card modal & Markdown | Modal opens from a card; title, priority, and description save; split-view live preview works; raw HTML is not rendered. |
| 8 | Subtasks | Add, edit, toggle done, delete; card shows done/total count. |
| 9 | Future-view stubs | Board / Flowchart / Vision Board tabs navigate; stub pages render without errors. |
| 10 | OAuth stub | "Sign in with Google" button reaches `/auth/google`, which returns the 501 page. |
| 11 | Polish & docs | README covers setup and commands; all tests pass; Ruff clean; `requirements.lock` committed. |

**Post-MVP:** Flowchart view, Vision board view (with image uploads to `data/uploads/`), calling the local model from the app.

---

## 9. Testing & Definition of Done

### 9.1 Strategy
| Kind | Tool | Covers |
|------|------|--------|
| Route & service tests | `pytest` + FastAPI `TestClient` against a temporary SQLite file | Every slice: status codes, persistence, business rules |
| Manual smoke test | Browser at `http://localhost:8000` | Drag and drop, modal behavior, visual layout |

### 9.2 Test Setup
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db, make_engine
from app.main import app


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    creds = {"email": "test@example.com", "password": "pass12345"}
    client.post("/register", data=creds)
    client.post("/login", data=creds)
    return client
```

### 9.3 Example Tests
```python
# tests/test_projects.py
def test_board_requires_login(client):
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_create_project_adds_complete_column(auth_client):
    res = auth_client.post("/projects", data={"name": "Demo"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Demo" in res.text
    assert "Complete" in res.text
```

### 9.4 Definition of Done
- `docker compose exec web pytest` passes.
- `ruff check .` and `ruff format --check .` are clean.
- Manual smoke test of the slice succeeds in the browser.
- Committed with a descriptive message.

---

## 10. Rules for the Model

1. **Work on one slice at a time.** Modify only files related to the current slice.
2. **Do not change the schema, add dependencies, or change versions without asking.** Propose the change and wait for approval.
3. **Use only the pinned versions in §2.** Write code for those exact versions: SQLAlchemy 2.0 style (`select()`, `Mapped[]`, `mapped_column()`), Pydantic v2, HTMX 2 attribute syntax. Do not use APIs from other versions.
4. **Stay inside the stack.** No Node, npm, React, TypeScript, bundlers, Tailwind, Redis, or Postgres. No CDN links; JavaScript comes only from `app/static/vendor/`.
5. **HTMX routes return HTML fragments, not JSON** (except `/healthz`).
6. **Respect the layers in §6.** Queries and business rules go in `services/`; routes handle HTTP and templates.
7. **Show only changed files, each in full.** Give the complete contents of every added or modified file, with its path, so it can be pasted directly.
8. **Ask when something in the spec is unclear instead of guessing.**

---

## 11. Decisions Log & Open Questions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-11-12 | Split-view Markdown editor (like Obsidian) | Instant visual feedback; matches user preference. |
| 2026-11-12 | OAuth deferred to a stub | Keeps the MVP focused; can be enabled later. |
| 2026-11-16 | Python 3.12 + FastAPI, server-rendered with Jinja2 + HTMX + Alpine.js | One language for all logic, no frontend build step; well represented in local-model training data. |
| 2026-11-16 | SQLite via SQLAlchemy 2.0 + Alembic | No database server; one file in a volume; versioned docs; migrations from day one. |
| 2026-11-16 | Single container, Docker Compose, port bound to `127.0.0.1` | Self-contained and only reachable from this machine. |
| 2026-11-16 | Session cookie (Starlette `SessionMiddleware`) + Argon2 hashing | Fits server-rendered pages better than tokens; Argon2 is a current recommended algorithm. |
| 2026-11-16 | JavaScript libraries vendored and pinned in `static/vendor/` | Works offline; versions cannot drift. |
| 2026-11-16 | Integer primary keys | Simplest option for SQLite and for readable URLs. |
| 2026-11-16 | Shared `cards` table + per-view layout tables | Future views reference cards instead of duplicating them. |
| 2026-11-16 | Server-side Markdown rendering with raw HTML disabled | One renderer for preview and display; prevents script injection. |
| 2026-11-16 | pytest + TestClient; no browser E2E suite in MVP | Covers behavior with minimal tooling; drag and drop verified by manual smoke test. |
| 2026-11-17 | Dockerfile installs from `requirements.lock` (full `pip freeze` of the resolved set) | Locks transitive deps so builds never re-resolve; eliminates resolver and network flakiness at build time (root cause of past failed attempts). |
| 2026-11-17 | Code baked into the image; dev loop is `docker compose up -d --build`; no code bind-mounts, no `--reload` | Avoids flaky macOS file-watching over bind mounts; cached rebuilds are a couple of seconds. |
| 2026-11-17 | Compose adds a stdlib-only healthcheck (urllib → `/healthz`); `data/.gitkeep` committed | `docker compose ps` reports true liveness; the `./data` mount target always exists and is user-owned. |
| 2026-11-17 | Registration closes after the first account (open Q2 resolved: yes) | ~10 lines; prevents a second account from silently breaking single-user assumptions. |
| 2026-11-17 | *Complete* column always renders rightmost, excluded from reordering (open Q1 resolved: yes) | Matches the spec's recommended approach; simplest consistent rule. |
| 2026-11-18 | `base.html` boot-status used a ternary with no else branch (a SyntaxError — the listener never registered even though all three vendor libraries loaded fine) | Caught by a jsdom run against the live app; the status line now has an explicit failure branch and always updates. |

### Open Questions
| # | Question | Recommended approach |
|---|----------|----------------------|
| 1 | Should the *Complete* column always stay rightmost? | **Resolved 2026-11-17: yes** — excluded from reordering, always rendered last. |
| 2 | Should registration close after the first account? | **Resolved 2026-11-17: yes** — reject `/register` once `users` is non-empty. |
| 3 | Concurrent edits (two tabs editing one card) | Low risk for a single user; defer. If needed, use SQLAlchemy's `version_id_col` and return 409 on mismatch. |
| 4 | Where do vision-board images live? | Files in `data/uploads/`, path in `board_items.image_path`, served by an authenticated route. |
