"""Slice 5: columns — add, rename, delete, reorder (SPEC §8, §4.2)."""


def test_create_column_requires_login(client) -> None:
    res = client.post(
        "/projects/1/columns", data={"name": "Backlog"}, follow_redirects=False
    )
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_create_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.post(
        "/projects/1/columns", data={"name": "Backlog"}, follow_redirects=False
    )
    assert res.status_code == 200
    assert "Backlog" in res.text
    page = auth_client.get("/projects/1")
    assert "Backlog" in page.text


def test_create_column_empty_name(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.post(
        "/projects/1/columns", data={"name": "   "}, follow_redirects=False
    )
    assert res.status_code == 400
    page = auth_client.get("/projects/1").text
    assert "Backlog" not in page


def test_create_column_missing_project(auth_client) -> None:
    res = auth_client.post(
        "/projects/999/columns", data={"name": "Backlog"}, follow_redirects=False
    )
    assert res.status_code == 404


def test_new_column_renders_before_complete(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    page = auth_client.get("/projects/1").text
    # column 2 (Backlog) renders before the locked column 1 (Complete).
    assert page.index('id="column-2"') < page.index('id="column-1"')


def test_rename_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    res = auth_client.patch(
        "/columns/2",
        data={"name": "Inbox"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert res.status_code == 200
    assert "Inbox" in res.text
    page = auth_client.get("/projects/1").text
    assert "Inbox" in page
    assert "Backlog" not in page


def test_rename_column_requires_login(client) -> None:
    res = client.patch(
        "/columns/1", data={"name": "X"}, follow_redirects=False
    )
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_rename_column_empty_name(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    res = auth_client.patch(
        "/columns/2", data={"name": "  "}, follow_redirects=False
    )
    assert res.status_code == 400


def test_rename_complete_column_forbidden(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.patch(
        "/columns/1", data={"name": "Done!"}, follow_redirects=False
    )
    assert res.status_code == 400
    page = auth_client.get("/projects/1").text
    assert "Complete" in page
    assert "Done!" not in page


def test_rename_missing_column(auth_client) -> None:
    res = auth_client.patch(
        "/columns/999", data={"name": "X"}, follow_redirects=False
    )
    assert res.status_code == 404


def test_delete_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    res = auth_client.delete(
        "/columns/2", headers={"HX-Request": "true"}, follow_redirects=False
    )
    assert res.status_code == 200
    page = auth_client.get("/projects/1").text
    assert "Backlog" not in page
    assert "Complete" in page


def test_delete_column_browser_redirects_to_board(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    res = auth_client.delete("/columns/2", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/projects/1"


def test_delete_column_requires_login(client) -> None:
    res = client.delete("/columns/1", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_delete_complete_column_forbidden(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.delete(
        "/columns/1", headers={"HX-Request": "true"}, follow_redirects=False
    )
    assert res.status_code == 400
    assert "Complete" in auth_client.get("/projects/1").text


def test_delete_missing_column(auth_client) -> None:
    res = auth_client.delete("/columns/999", follow_redirects=False)
    assert res.status_code == 404


def test_reorder_columns(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/projects/1/columns", data={"name": "B"})
    res = auth_client.post(
        "/projects/1/columns/reorder",
        data={"column_ids": ["3", "2"]},
        follow_redirects=False,
    )
    assert res.status_code == 204
    page = auth_client.get("/projects/1").text
    # B (column 3) now leads, and Complete (column 1) is still last.
    assert page.index('id="column-3"') < page.index('id="column-2"')
    assert page.index('id="column-2"') < page.index('id="column-1"')


def test_reorder_columns_requires_login(client) -> None:
    res = client.post(
        "/projects/1/columns/reorder",
        data={"column_ids": ["1"]},
        follow_redirects=False,
    )
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_reorder_rejects_complete_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    res = auth_client.post(
        "/projects/1/columns/reorder",
        data={"column_ids": ["1", "2"]},
        follow_redirects=False,
    )
    assert res.status_code == 400


def test_reorder_rejects_unknown_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    res = auth_client.post(
        "/projects/1/columns/reorder",
        data={"column_ids": ["2", "999"]},
        follow_redirects=False,
    )
    assert res.status_code == 400
