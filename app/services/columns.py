"""Column queries and business rules (SPEC §3.4, §4.2).

*Complete* is locked: it always renders rightmost and can never be renamed
or deleted (SPEC §11, Q1 resolved 2026-11-17).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Column, Project
from app.services.projects import get_project


def get_column(db: Session, column_id: int, user_id: int) -> Column | None:
    """Fetch one column scoped to the user's projects; None when missing."""
    column = db.get(Column, column_id)
    if column is None:
        return None
    project = db.get(Project, column.project_id)
    if project is None or project.user_id != user_id:
        return None
    return column


def _renumber(db: Session, project_id: int) -> None:
    """Renumber a project's columns: user columns 0..k-1, *Complete* at k.

    The caller commits, so the renumbering lands in the same transaction as
    the change that triggered it (SPEC §3.4).
    """
    columns = list(
        db.scalars(select(Column).where(Column.project_id == project_id)).all()
    )
    user_columns = [column for column in columns if not column.is_complete]
    for position, column in enumerate(user_columns):
        column.position = position
    for column in columns:
        if column.is_complete:
            column.position = len(user_columns)


def create_column(
    db: Session, project_id: int, user_id: int, name: str
) -> Column | None:
    """Add a column before *Complete*; None when the project is missing."""
    if get_project(db, project_id, user_id) is None:
        return None
    user_count = db.scalar(
        select(func.count(Column.id)).where(
            Column.project_id == project_id, Column.is_complete.is_(False)
        )
    )
    column = Column(
        project_id=project_id,
        name=name.strip(),
        position=user_count or 0,
        is_complete=False,
    )
    db.add(column)
    db.flush()
    _renumber(db, project_id)
    db.commit()
    return column


def rename_column(
    db: Session, column_id: int, user_id: int, name: str
) -> Column | None:
    """Rename a column; None when missing or when it is locked *Complete*."""
    column = get_column(db, column_id, user_id)
    if column is None or column.is_complete:
        return None
    column.name = name.strip()
    db.commit()
    return column


def delete_column(db: Session, column_id: int, user_id: int) -> Column | None:
    """Delete an empty column; None when missing, locked, or non-empty."""
    column = get_column(db, column_id, user_id)
    if column is None or column.is_complete or column.cards:
        return None
    project_id = column.project_id
    db.delete(column)
    db.flush()
    _renumber(db, project_id)
    db.commit()
    return column


def reorder_columns(
    db: Session, project_id: int, user_id: int, column_ids: list[int]
) -> bool:
    """Apply the new order of a project's user columns.

    The ids must be exactly the project's user columns — *Complete* is
    repositioned last here, never moved by the caller (SPEC §11, Q1).
    Returns False when the project is missing or the ids do not match.
    """
    project = get_project(db, project_id, user_id)
    if project is None:
        return False
    by_id = {column.id: column for column in project.columns}
    user_ids = {cid for cid, column in by_id.items() if not column.is_complete}
    if set(column_ids) != user_ids or len(column_ids) != len(user_ids):
        return False
    for position, column_id in enumerate(column_ids):
        by_id[column_id].position = position
    for column in by_id.values():
        if column.is_complete:
            column.position = len(column_ids)
    db.commit()
    return True
