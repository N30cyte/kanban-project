"""Engine, session factory, and declarative base (SPEC §3.5, §6)."""

from collections.abc import Iterator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base shared by all models and Alembic autogenerate."""


def make_engine(url: str) -> Engine:
    """Create an engine.

    SQLite does not enforce foreign keys unless asked (SPEC §3.5), so the
    ``PRAGMA foreign_keys=ON`` is registered on every connection. The
    ``check_same_thread=False`` argument is SQLite-only, hence the URL guard
    (the app is SQLite-only per SPEC §10 rule 4, the guard is cheap).
    """
    is_sqlite = url.startswith("sqlite")
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if is_sqlite else {},
    )

    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_conn: Any, _record: Any) -> None:
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


engine = make_engine(settings.database_url)

# expire_on_commit=False keeps ORM attributes usable in templates after a
# commit (server-rendered pages read models after handlers commit).
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding one session per request."""
    with SessionLocal() as session:
        yield session
