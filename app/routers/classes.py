from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.config import get_settings
from app.database import get_session
from app.models.class_ import Class
from app.rate_limiting import get_rate_limiter_service
from app.schemas.class_ import ClassJoin, ClassPublic
from app.schemas.sessions import AppSession
from app.security import (
    get_password_security,
    get_session_manager,
    get_viewer_dependencies,
)
from app.services import HomeworkService, StaffService
from app.tools.time_tools import get_week_range, resolve_date_parameters

router = APIRouter(prefix="", tags=["Classes"])
templates = Jinja2Templates(directory="app/templates/classes")

viewer_deps = get_viewer_dependencies()
session_manager = get_session_manager()
password_security = get_password_security()
rate_limiter = get_rate_limiter_service()
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
    _=Depends(rate_limiter.get_limiter_dependency),
):
    db_class = db_session.get(Class, data.id)

    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    if not await password_security.verify_password(
        data.password, db_class.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Wrong password")

    await session_manager.invalidate_session(request, response)
    await session_manager.issue_session(
        response, AppSession.from_class(request, db_class)
    )

    return db_class


@router.get("/exit/")
async def logout(request: Request):
    response = RedirectResponse(url="/classes", status_code=303)
    await session_manager.invalidate_session(request, response)
    return response


@router.get("/{class_id}/", response_class=HTMLResponse)
def get_class(
    request: Request,
    class_id: int,
    year: int | None = Query(None),
    week: int | None = Query(None),
    day: date_type | None = Query(None),
    db_session: Session = Depends(get_session),
    viewer: AppSession = Depends(viewer_deps.require_class_any),
):
    db_class = db_session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    selected_year, selected_week, selected_day = resolve_date_parameters(
        year, week, day
    )
    start_date, end_date = get_week_range(selected_year, selected_week, selected_day)

    staff_of_the_month = StaffService.get_best_staff_by_dates(
        db_session, class_id, start_date, end_date
    )

    homework_list = HomeworkService.get_by_dates(
        db_session, class_id, start_date, end_date
    )

    return templates.TemplateResponse(
        request=request,
        name="class_details.html",
        context={
            "class_item": ClassPublic.model_validate(db_class),
            "best_staff_username": staff_of_the_month.username
            if staff_of_the_month
            else None,
            "homework_list": homework_list,
            "selected_year": selected_year,
            "selected_week": selected_week,
            "selected_day": selected_day,
            "week_start_date": start_date.strftime("%d.%m"),
            "week_end_date": end_date.strftime("%d.%m"),
            "viewer": viewer,
        },
    )


@router.get("/{class_id}/homework/", response_class=HTMLResponse)
def get_homework_for_week(
    request: Request,
    class_id: int,
    year: int | None = Query(None),
    week: int | None = Query(None),
    day: date_type | None = Query(None),
    db_session: Session = Depends(get_session),
    viewer: AppSession = Depends(viewer_deps.require_class_any),
):

    db_class = db_session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    selected_year, selected_week, selected_day = resolve_date_parameters(
        year, week, day
    )
    start_date, end_date = get_week_range(selected_year, selected_week, selected_day)

    homework_list = HomeworkService.get_by_dates(
        db_session, class_id, start_date, end_date
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/homework_list.html",
        context={
            "class_item": ClassPublic.model_validate(db_class),
            "homework_list": homework_list,
            "selected_year": selected_year,
            "selected_week": selected_week,
            "selected_day": selected_day,
            "week_start_date": start_date.strftime("%d.%m"),
            "week_end_date": end_date.strftime("%d.%m"),
            "viewer": viewer,
        },
    )
