"""Password hashing and the current-user dependency (SPEC §4, §6).

Unauthenticated requests are bounced to ``/login``: normal requests get
``303``, HTMX requests (``HX-Request: true``) get ``200`` + ``HX-Redirect``.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, Response

from app.db import get_db
from app.models import User

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Argon2id hash of a plaintext password (SPEC §2.2, §3.1)."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """True when ``password`` matches ``password_hash``; False otherwise."""
    try:
        return _hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


class AuthenticationRequired(Exception):
    """No logged-in user; the app-level handler turns this into a redirect."""


def auth_required_response(request: Request) -> Response:
    """303 for normal requests, 200 + HX-Redirect for HTMX (SPEC §4)."""
    if request.headers.get("HX-Request") == "true":
        return Response(status_code=200, headers={"HX-Redirect": "/login"})
    return RedirectResponse("/login", status_code=303)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI dependency: the logged-in user, else AuthenticationRequired."""
    user_id: int | None = request.session.get("user_id")
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        if user_id is not None:
            request.session.clear()  # stale id: the account no longer exists
        raise AuthenticationRequired()
    return user
