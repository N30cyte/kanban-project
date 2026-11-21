"""Project routes: create, board, rename, delete (SPEC §4.2)."""

from fastapi import APIRouter, Depends, Form, HTTPException, Path
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, Response

from app.auth import current_user
from app.db import get_db
from app.models import User
from app.services.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    rename_project,
)

from starlette.requests import Request

router = APIRouter(dependencies=[Depends(current_user)])


def _templates(request: Request) -> Jinja2Templates:
    # app.state (not app.main) to avoid a circular import: main includes us.
    return request.app.state.templates


@router.post("/projects")
def create(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    name: str = Form(""),
) -> Response:
    """Create a project (with a locked *Complete* column); 303 to its board."""
    name = name.strip()
    if not name:
        return _templates(request).TemplateResponse(
            request=request,
            name="index.html",
            context={"error": "Enter a project name."},
            status_code=400,
        )
    project = create_project(db, user.id, name)
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)


@router.get("/projects/{project_id}")
def board(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    project_id: int = Path(...),
) -> Response:
    """Board page: sidebar (projects, new project, logout), header, columns, cards."""
    project = get_project(db, project_id, user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    columns = list(project.columns)
    return _templates(request).TemplateResponse(
        request=request,
        name="board.html",
        context={
            "project": project,
            "columns": columns,
            "projects": list_projects(db, user.id),
        },
    )


@router.patch("/projects/{project_id}")
def rename(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    project_id: int = Path(...),
    name: str = Form(""),
) -> Response:
    """Rename a project; the response is the board-header fragment."""
    name = name.strip()
    project = get_project(db, project_id, user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not name:
        return _templates(request).TemplateResponse(
            request=request,
            name="partials/board_header.html",
            context={"project": project, "error": "Enter a project name."},
            status_code=400,
        )
    updated = rename_project(db, project_id, user.id, name)
    return _templates(request).TemplateResponse(
        request=request,
        name="partials/board_header.html",
        context={"project": updated},
        status_code=200,
    )


@router.delete("/projects/{project_id}")
def delete(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    project_id: int = Path(...),
) -> Response:
    """Delete a project; HTMX gets HX-Redirect, browsers get a redirect."""
    project = get_project(db, project_id, user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    delete_project(db, project_id, user.id)
    if request.headers.get("HX-Request") == "true":
        return Response(status_code=200, headers={"HX-Redirect": "/"})
    return RedirectResponse(url="/", status_code=303)
