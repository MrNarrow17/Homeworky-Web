from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, col, select

from app.config import get_settings
from app.database import get_session
from app.models.class_ import Class
from app.models.homework import Homework
from app.models.sessions import SessionType
from app.schemas.class_ import ClassJoin, ClassPublic
from app.schemas.sessions import ViewerContext
from app.security import get_class_security
from app.tools.time_tools import get_week_range

router = APIRouter(prefix="", tags=["Classes"])
templates = Jinja2Templates(directory="app/templates/classes")

class_security = get_class_security()
settings = get_settings()


@router.get("/", response_class=HTMLResponse)
async def get_classes(
    request: Request,
    session: Session = Depends(get_session),
    context: ViewerContext | None = Depends(class_security.get_view_context),
):
    """
    An endpoint representing the class browser.

    Responses:
        - 307: Redirect to staff dashboard or class page.
        - 200: HTML response with the list of classes.
    """
    if context:
        return RedirectResponse(
            url="/staff/dashboard"
            if context.is_staff
            else f"/classes/{context.class_id}"
        )

    db_classes = session.exec(select(Class)).all()
    safe_classes = [ClassPublic.model_validate(c) for c in db_classes]
    return templates.TemplateResponse(
        request=request, name="classes.html", context={"classes": safe_classes}
    )


@router.post("/join/", response_model=ClassPublic)
async def join_class(
    data: ClassJoin,
    request: Request,
    response: Response,
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for joining a class.

    Responses:
        - 200: Class joined successfully.
        - 404: Class not found.
        - 401: Wrong password.
    """

    db_class = db_session.get(Class, data.id)

    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    if not class_security.verify_password(data.password, db_class.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong password")

    class_security.invalidate_session(request, response, db_session)
    class_security.issue_session(response, SessionType.CLASS, db_class.id, db_session)

    return db_class


@router.get("/exit/")
def logout(
    request: Request, response: Response, db_session: Session = Depends(get_session)
):
    """
    An endpoint for logging out of the class.

    Responses:
        - 303: Redirect to classes page.
    """

    response = RedirectResponse(url="/classes", status_code=303)
    class_security.invalidate_session(request, response, db_session)
    return response


@router.get("/{class_id}/", response_class=HTMLResponse)
async def get_class(
    request: Request,
    class_id: int,
    week: int | None = None,
    db_session: Session = Depends(get_session),
    viewer: ViewerContext = Depends(class_security.require_session),
):
    """
    An endpoint for viewing a class.

    Responses:
        - 200: HTML response with the class details.
        - 403: Wrong class.
        - 401: Unauthorized.
        - 404: Class not found.
    """
    db_class = db_session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    now = settings.current_time
    current_year, current_week, _ = now.isocalendar()

    selected_week = week if week is not None else current_week
    start_date, end_date = get_week_range(current_year, selected_week)

    statement = (
        select(Homework)
        .where(Homework.class_id == class_id)
        .where(Homework.date >= start_date)
        .where(Homework.date <= end_date)
        .order_by(col(Homework.created_at))
    )
    homework_list = db_session.exec(statement).all()

    return templates.TemplateResponse(
        request=request,
        name="class_details.html",
        context={
            "request": request,
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
    session: Session = Depends(get_session),
    viewer: ViewerContext = Depends(class_security.require_session),
):
    """
    An endpoint for viewing homework for a specific week.

    Responses:
        - 200: HTML response with the homework list.
        - 403: Wrong class.
        - 401: Unauthorized.
        - 404: Class not found.
    """

    db_class = session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    now = settings.current_time
    current_year, _, _ = now.isocalendar()

    start_date, end_date = get_week_range(current_year, week)

    statement = (
        select(Homework)
        .where(Homework.class_id == class_id)
        .where(Homework.date >= start_date)
        .where(Homework.date <= end_date)
        .order_by(col(Homework.date))
    )
    homework_list = session.exec(statement).all()

    return templates.TemplateResponse(
        request=request,
        name="partials/homework_list.html",
        context={
            "request": request,
            "class_item": ClassPublic.model_validate(db_class),
            "homework_list": homework_list,
            "current_week": week,
            "week_start_date": start_date.strftime("%d.%m"),
            "week_end_date": end_date.strftime("%d.%m"),
            "viewer": viewer,
        },
    )
