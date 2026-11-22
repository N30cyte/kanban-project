"""Column routes: add, rename, delete, reorder (SPEC §4.2)."""

from fastapi import APIRouter, Depends, Form, HTTPException, Path
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.auth import current_user
from app.db import get_db
from app.models import User
from app.services.columns import (
    create_column,
    delete_column,
    get_column,
    rename_column,
    reorder_columns,
)
from app.services.projects import get_project

router = APIRouter(dependencies=[Depends(current_user)])


def _templates(request: Request) -> Jinja2Templates:
    # app.state (not app.main) to avoid a circular import: main includes us.
    return request.app.state.templates


@router.post("/projects/{project_id}/columns")
def create(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    project_id: int = Path(...),
    name: str = Form(""),
) -> Response:
    """Add a column before *Complete*; the response is the new column fragment."""
    project = get_project(db, project_id, user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    name = name.strip()
    if not name:
        return _templates(request).TemplateResponse(
            request=request,
            name="partials/board_header.html",
            context={"project": project, "error": "Enter a column name."},
            status_code=400,
        )
    column = create_column(db, project_id, user.id, name)
    return _templates(request).TemplateResponse(
        request=request,
        name="partials/column.html",
        context={"column": column},
        status_code=200,
    )


@router.post("/projects/{project_id}/columns/reorder")
def reorder(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    project_id: int = Path(...),
    column_ids: list[int] = Form(default_factory=list),
) -> Response:
    """Apply the new order of the user columns; *Complete* stays last (204)."""
    if not reorder_columns(db, project_id, user.id, column_ids):
        raise HTTPException(status_code=400, detail="Invalid column order")
    return Response(status_code=204)


@router.patch("/columns/{column_id}")
def rename(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    column_id: int = Path(...),
    name: str = Form(""),
) -> Response:
    """Rename a column; the response is the column-header fragment."""
    column = get_column(db, column_id, user.id)
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    if column.is_complete:
        return _templates(request).TemplateResponse(
            request=request,
            name="partials/column_header.html",
            context={
                "column": column,
                "error": "The Complete column is locked.",
            },
            status_code=400,
        )
    name = name.strip()
    if not name:
        return _templates(request).TemplateResponse(
            request=request,
            name="partials/column_header.html",
            context={"column": column, "error": "Enter a column name."},
            status_code=400,
        )
    updated = rename_column(db, column_id, user.id, name)
    return _templates(request).TemplateResponse(
        request=request,
        name="partials/column_header.html",
        context={"column": updated},
        status_code=200,
    )


@router.delete("/columns/{column_id}")
def delete(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    column_id: int = Path(...),
) -> Response:
    """Delete an empty column; HTMX gets 200, browsers get a 303 to the board."""
    column = get_column(db, column_id, user.id)
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    if column.is_complete:
        return Response(status_code=400, content="The Complete column is locked.")
    if column.cards:
        return Response(
            status_code=400, content="Delete the column's cards first."
        )
    project_id = column.project_id
    delete_column(db, column_id, user.id)
    if request.headers.get("HX-Request") == "true":
        return Response(status_code=200)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
