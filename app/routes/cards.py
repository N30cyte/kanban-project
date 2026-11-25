"""Card routes: add, move (drag within / across columns) (SPEC §4.2)."""

from fastapi import APIRouter, Depends, Form, HTTPException, Path
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

from app.auth import current_user
from app.db import get_db
from app.models import User
from app.services.cards import create_card, move_card
from app.services.columns import get_column

router = APIRouter(dependencies=[Depends(current_user)])


def _templates(request: Request) -> Jinja2Templates:
    # app.state (not app.main) to avoid a circular import: main includes us.
    return request.app.state.templates


@router.post("/columns/{column_id}/cards")
def create(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    column_id: int = Path(...),
    title: str = Form(""),
) -> Response:
    """Add a card to the column; the response is the new card fragment."""
    column = get_column(db, column_id, user.id)
    if column is None or column.is_complete:
        raise HTTPException(status_code=404, detail="Column not found")
    title = title.strip()
    if not title:
        return Response(status_code=400, content="Enter a card title.")
    card = create_card(db, column_id, user.id, title)
    return _templates(request).TemplateResponse(
        request=request,
        name="partials/card.html",
        context={"card": card},
        status_code=200,
    )


@router.post("/cards/move")
def move(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    card_id: int = Form(...),
    to_column_id: int = Form(...),
    card_ids: list[int] = Form(default_factory=list),
) -> Response:
    """Apply the new order after a card drag; *Complete* is not a move target (204)."""
    if not move_card(db, card_id, user.id, to_column_id, card_ids):
        raise HTTPException(status_code=400, detail="Invalid card move")
    return Response(status_code=204)
