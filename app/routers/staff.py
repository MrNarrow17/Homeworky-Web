import os
import uuid
from typing import Annotated

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    Form,
    Response,
    status,
)
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, col, select

from app.config import get_settings
from app.database import get_session
from app.models.class_ import Class
from app.models.homework import Homework
from app.models.staff import Staff
from app.rate_limiting import get_rate_limiter_service
from app.schemas.class_ import ClassPublic
from app.schemas.homework import HomeworkForm
from app.schemas.sessions import AppSession
from app.schemas.staff import LoginRequest, LoginResponse
from app.security import (
    get_password_security,
    get_session_manager,
    get_viewer_dependencies,
)
from app.services import HomeworkService
from app.tools.time_tools import get_week_range

router = APIRouter(prefix="/staff", tags=["Staff"])
templates = Jinja2Templates(directory="app/templates/staff")

viewer_deps = get_viewer_dependencies()
session_manager = get_session_manager()
password_security = get_password_security()
rate_limiter = get_rate_limiter_service()
settings = get_settings()


@router.get("/login/", response_class=HTMLResponse)
async def staff_login(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login/", response_model=LoginResponse)
async def staff_login_post(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    db_session: Session = Depends(get_session),
    _=Depends(rate_limiter.get_limiter_dependency),
):
    staff = db_session.exec(
        select(Staff).where(Staff.username == credentials.username)
    ).first()
    if not staff or not await password_security.verify_password(
        credentials.password, staff.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await session_manager.invalidate_session(request, response)
    await session_manager.issue_session(response, AppSession.from_staff(request, staff))

    return LoginResponse(redirect_url="/staff/dashboard")


@router.get("/logout/", response_class=RedirectResponse)
async def staff_logout(request: Request, db_session: Session = Depends(get_session)):
    response = RedirectResponse(url="/classes", status_code=303)
    await session_manager.invalidate_session(request, response)
    return response


@router.get("/dashboard/", response_class=HTMLResponse)
async def staff_dashboard_redirect(
    request: Request,
    viewer: AppSession = Depends(viewer_deps.require_staff),
    db_session: Session = Depends(get_session),
):

    statement = (
        select(Class).where(col(Class.id).in_(viewer.staff_class_ids))
        if viewer.is_mod
        else select(Class)
    )
    classes = db_session.exec(statement).all()
    return templates.TemplateResponse(
        request=request,
        name="staff_class_picker.html",
        context={
            "classes": [ClassPublic.model_validate(c) for c in classes],
            "staff_role": "Адміністратор" if viewer.is_admin else "Модератор",
        },
    )


@router.get("/classes/{class_id}/dashboard/", response_class=HTMLResponse)
async def class_dashboard(
    request: Request,
    class_id: int = Depends(viewer_deps.require_class_staff),
    db_session: Session = Depends(get_session),
):
    db_class = db_session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    now = settings.local_time
    current_year, current_week, _ = now.isocalendar()
    start_date, end_date = get_week_range(current_year, current_week)

    homework_count = HomeworkService.count_in_class(db_session, class_id)
    week_homework_count = HomeworkService.count_by_dates(
        db_session, class_id, start_date, end_date
    )

    context = {
        "request": request,
        "class_": ClassPublic.model_validate(db_class),
        "homework_count": homework_count,
        "week_homework_count": week_homework_count,
    }
    return templates.TemplateResponse(
        request=request, name="class_dashboard.html", context=context
    )


@router.get("/classes/{class_id}/homework/", response_class=HTMLResponse)
async def staff_homework(
    request: Request,
    class_id: int = Depends(viewer_deps.require_class_staff),
    db_session: Session = Depends(get_session),
):
    db_class = db_session.get(Class, class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    homework_list = HomeworkService.get_in_class(db_session, class_id)
    context = {
        "request": request,
        "homework_list": homework_list,
        "class_": ClassPublic.model_validate(db_class),
    }
    return templates.TemplateResponse(
        request=request, name="homework_list.html", context=context
    )


@router.get("/classes/{class_id}/homework/new/", response_class=HTMLResponse)
async def get_homework_form(
    request: Request,
    class_id: int = Depends(viewer_deps.require_class_staff),
):
    return templates.TemplateResponse(
        request=request,
        name="homework_form.html",
        context={"class_id": class_id, "homework": None},
    )


@router.post("/classes/{class_id}/homework/new/", response_class=RedirectResponse)
async def post_homework_form(
    request: Request,
    form: Annotated[HomeworkForm, Form()],
    viewer: AppSession = Depends(viewer_deps.require_staff),
    class_id: int = Depends(viewer_deps.require_class_staff),
    db_session: Session = Depends(get_session),
):
    staff = db_session.get(Staff, viewer.staff_id)
    if not staff:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Staff required")

    form_data = await request.form()
    raw_images = form_data.getlist("images")

    image_paths = []
    for img in raw_images:
        if not isinstance(img, str) and img.filename:
            ext = img.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join("uploads", filename)
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(await img.read())
            image_paths.append(f"/uploads/{filename}")
        elif isinstance(img, str):
            image_paths.append(img)

    new_homework = Homework(
        class_id_db=class_id,
        subject=form.subject,
        title=form.title,
        description=form.description,
        date=form.date,
        images=image_paths,
        created_by=staff.username,
    )
    db_session.add(new_homework)
    db_session.commit()

    return RedirectResponse(
        url=f"/staff/classes/{class_id}/dashboard/", status_code=303
    )


@router.get("/homework/{homework_id}/edit/", response_class=HTMLResponse)
async def get_edit_homework_form(
    request: Request,
    homework: Homework = Depends(viewer_deps.require_homework_staff),
):
    return templates.TemplateResponse(
        request=request,
        name="homework_form.html",
        context={"class_id": homework.class_id_db, "homework": homework},
    )


@router.post("/homework/{homework_id}/edit/")
async def post_edit_homework_form(
    request: Request,
    form: Annotated[HomeworkForm, Form()],
    homework: Homework = Depends(viewer_deps.require_homework_staff),
    db_session: Session = Depends(get_session),
):
    form_data = await request.form()
    raw_images = form_data.getlist("images")

    image_paths = []
    for img in raw_images:
        if not isinstance(img, str) and img.filename:
            ext = img.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join("uploads", filename)
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(await img.read())
            image_paths.append(f"/uploads/{filename}")
        elif isinstance(img, str) and img:
            image_paths.append(img)

    homework.subject = form.subject
    homework.title = form.title
    homework.description = form.description
    homework.date = form.date
    homework.images = image_paths

    db_session.add(homework)
    db_session.commit()

    return RedirectResponse(
        url=f"/staff/classes/{homework.class_id_db}/dashboard/", status_code=303
    )


@router.post("/homework/{homework_id}/delete/")
async def delete_homework(
    homework: Homework = Depends(viewer_deps.require_homework_staff),
    db_session: Session = Depends(get_session),
):
    class_id = homework.class_id_db
    db_session.delete(homework)
    db_session.commit()
    return RedirectResponse(
        url=f"/staff/classes/{class_id}/dashboard/", status_code=303
    )
