"""Card queries and business rules (SPEC §3.4, §4.2).

*Complete* is locked: it is never a destination for new cards or drags
(SPEC §11, Q1 resolved 2026-11-17).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Card, Column, Project
from app.services.columns import get_column


def get_card(db: Session, card_id: int, user_id: int) -> Card | None:
    """Fetch one card scoped to the user's projects; None when missing."""
    card = db.get(Card, card_id)
    if card is None:
        return None
    column = db.get(Column, card.column_id)
    if column is None:
        return None
    project = db.get(Project, column.project_id)
    if project is None or project.user_id != user_id:
        return None
    return card


def create_card(
    db: Session, column_id: int, user_id: int, title: str
) -> Card | None:
    """Add a card at the end of the column; None when it is missing or blank."""
    column = get_column(db, column_id, user_id)
    if column is None or column.is_complete:
        return None
    title = title.strip()
    if not title:
        return None
    position = db.scalar(
        select(func.count(Card.id)).where(Card.column_id == column.id)
    ) or 0
    card = Card(column_id=column.id, title=title, position=position)
    db.add(card)
    db.commit()
    return card


def move_card(
    db: Session, card_id: int, user_id: int, to_column_id: int, card_ids: list[int]
) -> bool:
    """Apply a drag: put the card at *card_ids*'s order inside *to_column_id*.

    *card_ids* is the destination column's full order after the move, the
    dragged card included at its new position (SPEC §4.2). Returns False
    when the card or the column is missing, or the order is invalid.
    """
    card = get_card(db, card_id, user_id)
    if card is None:
        return False
    to_column = get_column(db, to_column_id, user_id)
    if to_column is None or to_column.is_complete:
        return False
    if card_id not in card_ids:
        return False
    for next_id in card_ids:
        moved = db.get(Card, next_id)
        if moved is None:
            return False
        # Every card except the dragged one must already be in the
        # destination column; the dragged one is still in its source.
        if next_id != card_id and moved.column_id != to_column.id:
            return False
    source_column_id = card.column_id
    for position, card_id_next in enumerate(card_ids):
        db.get(Card, card_id_next).position = position
    card.column_id = to_column.id
    card.position = card_ids.index(card_id)
    if source_column_id != to_column.id:
        _renumber_cards(db, source_column_id)
    db.commit()
    return True


def _renumber_cards(db: Session, column_id: int) -> None:
    """Renumber a column's cards: 0..n-1 in position order.

    The caller commits, so the renumbering lands in the same transaction as the move that triggered it (SPEC §3.4).
    """
    cards = list(
        db.scalars(
            select(Card)
            .where(Card.column_id == column_id)
            .order_by(Card.position)
        ).all()
    )
    for position, card in enumerate(cards):
        card.position = position
