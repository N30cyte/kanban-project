"""Account business rules: registration and credential checks (SPEC §4.1, §11)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import hash_password, verify_password
from app.models import User


class RegistrationClosedError(Exception):
    """Raised when /register is called after the first account exists."""


def register(db: Session, email: str, password: str) -> User:
    """Create the first (and only) account.

    Registration closes once any user exists (SPEC §11, open question 2).
    """
    if db.scalar(select(func.count()).select_from(User)) > 0:
        raise RegistrationClosedError()
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the user when the credentials are valid, else None."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
