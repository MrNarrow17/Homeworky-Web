from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.config import get_settings
from app.database import get_session
from app.models.class_ import Class
from app.schemas.class_ import ClassJoin, ClassPublic
from app.schemas.sessions import AppSession
from app.security import (
    get_password_security,
    get_session_manager,
    get_viewer_dependencies,
)
from app.services import HomeworkService
from app.tools.time_tools import get_week_range

router = APIRouter(prefix="", tags=["Classes"])
templates = Jinja2Templates(directory="app/templates/classes")

viewer_deps = get_viewer_dependencies()
session_manager = get_session_manager()
password_security = get_password_security()
settings = get_settings()


@router.get("/", response_class=HTMLResponse)
async def get_classes(
    request: Request,
    db_session: Session = Depends(get_session),
    viewer: AppSession = Depends(viewer_deps.get_viewer),
):
    if viewer.is_authenticated:
        return RedirectResponse(
            url="/staff/dashboard" if viewer.is_staff else f"/classes/{viewer.class_id}"
        )

    db_classes = db_session.exec(select(Class)).all()
    safe_classes = [ClassPublic.model_validate(c) for c in db_classes]
    return templates.TemplateResponse(
        request=request,
        name="classes.html",
        context={"classes": safe_classes, "telegram": settings.telegram_link},
    )


@router.post("/join/", response_model=ClassPublic)
async def join_class(
    data: ClassJoin,
    request: Request,
    response: Response,
    db_session: Session = Depends(get_session),
):
    db_class = db_session.get(Class, data.id)

    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    if not password_security.verify_password(data.password, db_class.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong password")

    session_manager.invalidate_session(request, response)
    session_manager.issue_session(response, AppSession.from_class(request, db_class))

    return db_class


@router.get("/exit/")
def logout(request: Request, db_session: Session = Depends(get_session)):
    response = RedirectResponse(url="/classes", status_code=303)
    session_manager.invalidate_session(request, response)
    return response


@router.get("/{class_id}/", response_class=HTMLResponse)
async def get_class(
    request: Request,
    class_id: int,
    week: int | None = None,
    db_session: Session = Depends(get_session),
    viewer: AppSession = Depends(viewer_deps.require_class_any),
):
    db_class = db_session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    now = settings.current_time
    current_year, current_week, _ = now.isocalendar()

    selected_week = week if week is not None else current_week
    start_date, end_date = get_week_range(current_year, selected_week)

    homework_list = HomeworkService.get_by_dates(
        db_session, class_id, start_date, end_date
    )

    return templates.TemplateResponse(
        request=request,
        name="class_details.html",
        context={
            "class_item": ClassPublic.model_validate(db_class),
            "homework_list": homework_list,
            "current_week": selected_week,
            "week_start_date": start_date.strftime("%d.%m"),
            "week_end_date": end_date.strftime("%d.%m"),
            "viewer": viewer,
        },
    )


@router.get("/{class_id}/homework/", response_class=HTMLResponse)
def get_homework_for_week(
    request: Request,
    class_id: int,
    week: int = Query(...),
    db_session: Session = Depends(get_session),
    viewer: AppSession = Depends(viewer_deps.require_class_any),
):
    db_class = db_session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    now = settings.current_time
    current_year, _, _ = now.isocalendar()

    start_date, end_date = get_week_range(current_year, week)

    homework_list = HomeworkService.get_by_dates(
        db_session, class_id, start_date, end_date
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/homework_list.html",
        context={
            "class_item": ClassPublic.model_validate(db_class),
            "homework_list": homework_list,
            "current_week": week,
            "week_start_date": start_date.strftime("%d.%m"),
            "week_end_date": end_date.strftime("%d.%m"),
            "viewer": viewer,
        },
    )
