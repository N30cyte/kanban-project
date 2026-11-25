"""FastAPI app factory: middleware, static mount, templates, and routes."""

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, RedirectResponse, Response

from app.auth import AuthenticationRequired, auth_required_response, current_user
from app.config import settings
from app.db import get_db
from app.models import User
from app.routes.auth import router as auth_router
from app.routes.cards import router as cards_router
from app.routes.columns import router as columns_router
from app.routes.projects import router as projects_router
from app.services.projects import first_project

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="kanban")

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Shared via app.state so route modules can render without importing app.main
# (which would be circular: main includes the routers).
app.state.templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(columns_router)
app.include_router(cards_router)


@app.exception_handler(AuthenticationRequired)
def auth_required(request: Request, exc: AuthenticationRequired) -> Response:
    return auth_required_response(request)


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/")
def index(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Response:
    """303 to the first project's board, or the empty page (SPEC §4.1)."""
    first = first_project(db, user.id)
    if first is not None:
        return RedirectResponse(f"/projects/{first.id}", status_code=303)
    return app.state.templates.TemplateResponse(
        request=request, name="index.html", context={}
    )
