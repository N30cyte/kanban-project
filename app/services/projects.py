"""Project queries and business rules (SPEC §3.4, §4.2). Grows with Slice 4."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project


def first_project(db: Session, user_id: int) -> Project | None:
    """The user's earliest project — the target of the / redirect (SPEC §4.1)."""
    return db.scalar(
        select(Project).where(Project.user_id == user_id).order_by(Project.id).limit(1)
    )
