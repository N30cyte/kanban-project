"""Slice 6: cards — add, move within / across columns (SPEC §8, §4.2)."""


def test_create_card_requires_login(client) -> None:
    res = client.post(
        "/columns/1/cards", data={"title": "Fix bug"}, follow_redirects=False
    )
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_create_card(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    res = auth_client.post(
        "/columns/2/cards", data={"title": "Ship v1"}, follow_redirects=False
    )
    assert res.status_code == 200
    assert "Ship v1" in res.text
    page = auth_client.get("/projects/1")
    assert "Ship v1" in page.text


def test_create_card_empty_title(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    res = auth_client.post(
        "/columns/2/cards", data={"title": "   "}, follow_redirects=False
    )
    assert res.status_code == 400
    assert "Backlog" in auth_client.get("/projects/1").text


def test_create_card_missing_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.post(
        "/columns/999/cards", data={"title": "X"}, follow_redirects=False
    )
    assert res.status_code == 404


def test_create_card_locked_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    res = auth_client.post(
        "/columns/1/cards", data={"title": "X"}, follow_redirects=False
    )
    assert res.status_code == 404


def test_create_card_appends_at_end(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    auth_client.post("/columns/2/cards", data={"title": "One"})
    auth_client.post("/columns/2/cards", data={"title": "Two"})
    auth_client.post("/columns/2/cards", data={"title": "Three"})
    page = auth_client.get("/projects/1").text
    assert page.index('id="card-1"') < page.index('id="card-2"')
    assert page.index('id="card-2"') < page.index('id="card-3"')


def test_move_card_requires_login(client) -> None:
    res = client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "2", "card_ids": ["1"]},
        follow_redirects=False,
    )
    assert res.status_code == 303
    assert res.headers["location"] == "/login"


def test_move_card_within_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "Backlog"})
    auth_client.post("/columns/2/cards", data={"title": "One"})
    auth_client.post("/columns/2/cards", data={"title": "Two"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "2", "card_ids": ["2", "1"]},
        follow_redirects=False,
    )
    assert res.status_code == 204
    # A fresh page render proves the order persisted in the database.
    page = auth_client.get("/projects/1").text
    assert page.index('id="card-2"') < page.index('id="card-1"')


def test_move_card_across_columns(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/projects/1/columns", data={"name": "B"})
    auth_client.post("/columns/2/cards", data={"title": "In A"})
    auth_client.post("/columns/3/cards", data={"title": "In B"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "3", "card_ids": ["1", "2"]},
        follow_redirects=False,
    )
    assert res.status_code == 204
    page = auth_client.get("/projects/1").text
    # Card 1 now renders inside column B (3), ahead of card 2.
    assert page.index('id="column-3"') < page.index('id="card-1"')
    assert page.index('id="card-1"') < page.index('id="card-2"')


def test_move_card_across_columns_reorder(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/projects/1/columns", data={"name": "B"})
    auth_client.post("/columns/2/cards", data={"title": "In A"})
    auth_client.post("/columns/3/cards", data={"title": "In B"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "3", "card_ids": ["2", "1"]},
        follow_redirects=False,
    )
    assert res.status_code == 204
    page = auth_client.get("/projects/1").text
    # Card 1 lands after card 2 in column B, and column A is empty.
    assert page.index('id="card-2"') < page.index('id="card-1"')


def test_move_missing_card(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "999", "to_column_id": "2", "card_ids": ["999"]},
        follow_redirects=False,
    )
    assert res.status_code == 400


def test_move_missing_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/columns/2/cards", data={"title": "X"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "999", "card_ids": ["1"]},
        follow_redirects=False,
    )
    assert res.status_code == 400


def test_move_rejects_complete_column(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/columns/2/cards", data={"title": "X"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "1", "card_ids": ["1"]},
        follow_redirects=False,
    )
    assert res.status_code == 400
    # The card stays where it was.
    page = auth_client.get("/projects/1").text
    assert page.index('id="column-2"') < page.index('id="card-1"')


def test_move_rejects_card_not_in_order(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/columns/2/cards", data={"title": "X"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "2", "card_ids": []},
        follow_redirects=False,
    )
    assert res.status_code == 400


def test_move_rejects_unknown_card_in_order(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/columns/2/cards", data={"title": "X"})
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "1", "to_column_id": "2", "card_ids": ["1", "999"]},
        follow_redirects=False,
    )
    assert res.status_code == 400


def test_move_rejects_foreign_card_in_order(auth_client) -> None:
    auth_client.post("/projects", data={"name": "Demo"})
    auth_client.post("/projects/1/columns", data={"name": "A"})
    auth_client.post("/projects/1/columns", data={"name": "B"})
    auth_client.post("/columns/2/cards", data={"title": "In A"})
    auth_client.post("/columns/3/cards", data={"title": "In B"})
    # Card 1 (in A) is part of the claimed order but not the dragged card.
    res = auth_client.post(
        "/cards/move",
        data={"card_id": "2", "to_column_id": "3", "card_ids": ["1", "2"]},
        follow_redirects=False,
    )
    assert res.status_code == 400
