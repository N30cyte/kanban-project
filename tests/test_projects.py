"""Slice4: projects — create, board, rename, delete (SPEC §8, §4.2)."""


def test_create_project_requires_login(client) -> None:
    res = client.post("/projects", data={"name": "Demo"}, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_create_project_redirects_to_board(auth_client) -> None:
    res = auth_client.post("/projects", data={"name": "Demo"}, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/projects/1"


def test_created_project_gets_locked_complete_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.get("/projects/1")
    assert res.status_code == 200
    assert "Demo" in res.text
    assert "Complete" in res.text


def test_board_renders_sidebar_and_columns(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.get("/projects/1")
    assert res.status_code == 200
    assert "Demo" in res.text
    assert "Complete" in res.text
    assert "New Project" in res.text


def test_board_requires_login(client) -> None:
    res = client.get("/projects/1", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_index_redirects_to_first_project(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.get("/", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/projects/1"


def test_rename_project(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.patch(
        "/projects/1",
        data={"name": "Demo 2"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert res.status_code == 200
    res = auth_client.get("/projects/1")
    assert "Demo 2" in res.text


def test_delete_project(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.delete(
        "/projects/1",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert res.status_code == 200
    assert res.headers["HX-Redirect"] == "/"
    res = auth_client.get("/", follow_redirects=False)
    assert res.status_code == 200
    assert "Create project" in res.text
