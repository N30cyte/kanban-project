"""Shared fixtures (SPEC §9.2).

``auth_client`` arrives with Slice 3, when /register and /login exist.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.db import Base, get_db, make_engine
from app.main import app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()
