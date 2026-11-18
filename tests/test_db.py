"""Slice 2: engine, models, and foreign-key behavior (SPEC §8, §9)."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.db import Base, make_engine


@pytest.fixture
def db(tmp_path: Path) -> Session:
    """A session on a fresh temp database, built through make_engine so the
    foreign-key pragma from SPEC §3.5 is in effect."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fk.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()


def _count(session: Session, model: Any) -> int:
    return len(session.execute(select(model)).scalars().all())


def test_healthz(client: TestClient) -> None:
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_all_core_tables_created(db: Session) -> None:
    names = set(inspect(db.get_bind()).get_table_names())
    assert {"users", "projects", "columns", "cards", "subtasks"} <= names


def test_foreign_keys_enforced(db: Session) -> None:
    db.add(models.Project(name="Orphan", user_id=9999))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert _count(db, models.Project) == 0


def test_delete_cascades_from_user(db: Session) -> None:
    user = models.User(email="u@example.com", password_hash="hash")
    db.add(user)
    db.commit()

    project = models.Project(user_id=user.id, name="Game One")
    db.add(project)
    db.commit()

    column = models.Column(project_id=project.id, name="Doing", position=0)
    db.add(column)
    db.commit()

    card = models.Card(column_id=column.id, title="Card", position=0)
    db.add(card)
    db.commit()

    subtask = models.Subtask(card_id=card.id, title="Sub", position=0)
    db.add(subtask)
    db.commit()

    db.delete(user)
    db.commit()

    assert _count(db, models.Project) == 0
    assert _count(db, models.Column) == 0
    assert _count(db, models.Card) == 0
    assert _count(db, models.Subtask) == 0


def test_priority_defaults_to_needs_assigning(db: Session) -> None:
    user = models.User(email="u@example.com", password_hash="hash")
    db.add(user)
    db.commit()
    project = models.Project(user_id=user.id, name="Game One")
    db.add(project)
    db.commit()
    column = models.Column(project_id=project.id, name="Doing", position=0)
    db.add(column)
    db.commit()
    card = models.Card(column_id=column.id, title="Card", position=0)
    db.add(card)
    db.commit()
    db.refresh(card)
    assert card.priority is models.Priority.needs_assigning
