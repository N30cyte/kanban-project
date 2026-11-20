"""Shared fixtures (SPEC §9.2)."""

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


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """A logged-in client: registers the first account, then logs in."""
    creds = {"email": "test@example.com", "password": "pass12345"}
    client.post("/register", data=creds)
    client.post("/login", data=creds)
    return client
