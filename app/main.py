"""FastAPI app factory: static mount, templates, and HTTP routes."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings  # noqa: F401  (consumed by later slices)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="kanban")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/")
def index(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="base.html", context={})
