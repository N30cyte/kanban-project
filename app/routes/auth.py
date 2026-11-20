"""Auth routes: /register, /login, /logout (SPEC §4.1)."""

import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, Response

from app.db import get_db
from app.services.users import RegistrationClosedError, authenticate, register

router = APIRouter()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _templates(request: Request) -> Jinja2Templates:
    # app.state (not app.main) to avoid a circular import: main includes us.
    return request.app.state.templates


def _page(
    request: Request,
    name: str,
    *,
    error: str | None = None,
    status_code: int = 200,
    email: str = "",
) -> Response:
    return _templates(request).TemplateResponse(
        request=request,
        name=name,
        context={"error": error, "email": email},
        status_code=status_code,
    )


@router.get("/register")
def register_page(request: Request) -> Response:
    return _page(request, "register.html")


@router.post("/register")
def register_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(""),
    password: str = Form(""),
) -> Response:
    email = email.strip().lower()
    if _EMAIL_RE.match(email) is None or not password:
        return _page(
            request,
            "register.html",
            error="Enter an email address and a password.",
            status_code=400,
            email=email,
        )
    try:
        register(db, email, password)
    except RegistrationClosedError:
        return _page(
            request,
            "register.html",
            error="Registration is closed — an account already exists.",
            status_code=409,
            email=email,
        )
    return RedirectResponse("/login", status_code=303)


@router.get("/login")
def login_page(request: Request) -> Response:
    return _page(request, "login.html")


@router.post("/login")
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(""),
    password: str = Form(""),
) -> Response:
    email = email.strip().lower()
    user = authenticate(db, email, password)
    if user is None:
        return _page(
            request,
            "login.html",
            error="Invalid email or password.",
            status_code=401,
            email=email,
        )
    request.session.clear()  # fresh session id on login
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
