"""Slice 3: auth — register, login, logout, and protected routes (SPEC §8)."""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import models
from app.auth import hash_password, verify_password
from app.db import make_engine

CREDS = {"email": "test@example.com", "password": "pass12345"}
OTHER = {"email": "second@example.com", "password": "another-pass"}


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("pass12345")
    assert hashed != "pass12345"
    assert verify_password("pass12345", hashed) is True
    assert verify_password("wrong-pass", hashed) is False
    assert verify_password("pass12345", "not-a-valid-hash") is False


def test_register_page_renders(client: TestClient) -> None:
    res = client.get("/register")
    assert res.status_code == 200
    assert "Create your account" in res.text


def test_register_invalid_input_is_400_page(client: TestClient) -> None:
    res = client.post("/register", data={"email": "nope", "password": ""})
    assert res.status_code == 400
    assert "email address and a password" in res.text


def test_register_success_redirects_to_login(client: TestClient) -> None:
    res = client.post("/register", data=CREDS, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_register_closes_after_first_account(client: TestClient) -> None:
    client.post("/register", data=CREDS)
    res = client.post("/register", data=OTHER, follow_redirects=False)
    assert res.status_code == 409
    assert "closed" in res.text.lower()


def test_login_success_redirects_home(client: TestClient) -> None:
    client.post("/register", data=CREDS)
    res = client.post("/login", data=CREDS, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/"


def test_login_bad_password_is_401_page(client: TestClient) -> None:
    client.post("/register", data=CREDS)
    res = client.post(
        "/login",
        data={"email": CREDS["email"], "password": "wrong-pass"},
        follow_redirects=False,
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.text


def test_login_unknown_email_is_401_page(client: TestClient) -> None:
    res = client.post(
        "/login",
        data={"email": "ghost@example.com", "password": "pass12345"},
        follow_redirects=False,
    )
    assert res.status_code == 401


def test_index_requires_login(client: TestClient) -> None:
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_index_htmx_gets_hx_redirect(client: TestClient) -> None:
    res = client.get("/", headers={"HX-Request": "true"}, follow_redirects=False)
    assert res.status_code == 200
    assert res.headers["HX-Redirect"] == "/login"


def test_index_authenticated_shows_empty_state(auth_client: TestClient) -> None:
    res = auth_client.get("/")
    assert res.status_code == 200
    assert "no projects" in res.text.lower()


def test_logout_ends_session(auth_client: TestClient) -> None:
    res = auth_client.post("/logout", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"
    res = auth_client.get("/", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_stale_session_user_id_is_cleared(client: TestClient, tmp_path: Path) -> None:
    client.post("/register", data=CREDS)
    client.post("/login", data=CREDS)
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    factory = sessionmaker(bind=engine)
    with factory() as db:
        db.query(models.User).delete()
        db.commit()
    engine.dispose()
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"
