"""Project queries and business rules (SPEC §3.4, §4.2). Grows with later slices."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Column, Project


COMPLETE_COLUMN_NAME = "Complete"


def first_project(db: Session, user_id: int) -> Project | None:
    """The user's earliest project — the target of the / redirect (SPEC §4.1)."""
    return db.scalar(
        select(Project).where(Project.user_id == user_id).order_by(Project.id).limit(1)
    )


def list_projects(db: Session, user_id: int) -> list[Project]:
    """All of the user's projects, oldest first (sidebar list, SPEC §5.1)."""
    return list(
        db.scalars(
            select(Project).where(Project.user_id == user_id).order_by(Project.id)
        )
    )


def create_project(db: Session, user_id: int, name: str) -> Project:
    """Create a project with a locked *Complete* column (SPEC §3.4)."""
    project = Project(user_id=user_id, name=name.strip())
    db.add(project)
    db.flush()
    db.add(
        Column(
            project_id=project.id,
            name=COMPLETE_COLUMN_NAME,
            position=0,
            is_complete=True,
        )
    )
    db.commit()
    return project


def get_project(db: Session, project_id: int, user_id: int) -> Project | None:
    """Fetch one project scoped to the user; None when missing (or not theirs)."""
    return db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )


def rename_project(
    db: Session, project_id: int, user_id: int, name: str
) -> Project | None:
    """Rename a project; None when it does not exist (or does not belong to the user)."""
    project = get_project(db, project_id, user_id)
    if project is None:
        return None
    project.name = name.strip()
    db.commit()
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    """Delete a project and its columns/cards via cascade."""
    project = get_project(db, project_id, user_id)
    if project is None:
        return
    db.delete(project)
    db.commit()
