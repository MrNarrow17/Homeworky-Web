import os
import uuid
from typing import Annotated

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Response,
)
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, col, func, select

from app.config import get_settings
from app.database import get_session
from app.models.homework import Homework
from app.models.staff import StaffMember
from app.schemas.class_ import ClassPublic
from app.schemas.homework import HomeworkForm
from app.schemas.sessions import ViewerContext
from app.schemas.staff import LoginRequest, LoginResponse
from app.security import (
    get_general_security,
    get_staff_security,
    get_viewer_dependencies,
)
from app.tools.time_tools import get_week_range

router = APIRouter(prefix="/staff", tags=["Staff"])
templates = Jinja2Templates(directory="app/templates/staff")

settings = get_settings()
general_security = get_general_security()
staff_security = get_staff_security()
viewer_deps = get_viewer_dependencies()


@router.get("/login/", response_class=HTMLResponse)
async def staff_login(request: Request):
    """
    An endpoint for displaying the login form.

    Responses:
        - 200: HTML response with the login form.
    """

    return templates.TemplateResponse(request, "login.html")


@router.post("/login/", response_model=LoginResponse)
async def staff_login_post(
    credentials: LoginRequest,
    response: Response,
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for logging in a staff member.

    Responses:
        - 200: Login successful, redirects to the dashboard.
        - 401: Invalid credentials.
    """

    staff_member = db_session.exec(
        select(StaffMember).where(StaffMember.username == credentials.username)
    ).first()
    if not staff_member or not general_security.verify_password(
        credentials.password, staff_member.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    staff_security.issue_session(response, staff_member.id, db_session)

    return LoginResponse(redirect_url="/staff/dashboard")


@router.get("/logout/", response_class=RedirectResponse)
async def staff_logout(request: Request, db_session: Session = Depends(get_session)):
    """
    An endpoint for logging out of a staff member account.

    Responses:
        - 303: Redirects to the classes page after logout.
    """

    response = RedirectResponse(url="/classes", status_code=303)
    staff_security.invalidate_session(request, response, db_session)
    return response


@router.get("/dashboard/", response_class=HTMLResponse)
async def staff_dashboard(
    request: Request,
    viewer: ViewerContext = Depends(viewer_deps.require_staff),
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for displaying the staff dashboard.

    Responses:
        - 200: HTML response with the dashboard content.
        - 401: Unauthorized.
        - 403: Wrong session type.
    """

    now = settings.current_time
    current_year, current_week, _ = now.isocalendar()

    start_date, end_date = get_week_range(current_year, current_week)

    staff_member = viewer.staff_member_verified

    homework_count = db_session.exec(
        select(func.count(Homework.id)).where(
            Homework.class_id == staff_member.class_id
        )
    ).one()

    week_homework_count = db_session.exec(
        select(func.count(Homework.id)).where(
            Homework.class_id == staff_member.class_id,
            Homework.date >= start_date,
            Homework.date <= end_date,
        )
    ).one()

    context = {
        "request": request,
        "staff": staff_member,
        "class_": ClassPublic.model_validate(staff_member.class_),
        "homework_count": homework_count,
        "week_homework_count": week_homework_count,
    }

    return templates.TemplateResponse(
        request=request, name="mod_dashboard.html", context=context
    )


@router.get("/homework/", response_class=HTMLResponse)
async def staff_homework(
    request: Request,
    viewer: ViewerContext = Depends(viewer_deps.require_staff),
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for displaying the staff homework list.

    Responses:
        - 200: HTML response with the homework list.
        - 401: Unauthorized.
        - 403: Wrong session type.
    """

    staff_member = viewer.staff_member_verified
    statement = (
        select(Homework)
        .where(Homework.class_id == staff_member.class_id)
        .order_by(col(Homework.date).desc())
    )
    homework_list = db_session.exec(statement).all()

    context = {
        "request": request,
        "homework_list": homework_list,
        "class_": ClassPublic.model_validate(staff_member.class_),
    }

    return templates.TemplateResponse(
        request=request, name="homework_list.html", context=context
    )


@router.get("/homework/new/", response_class=HTMLResponse)
async def get_homework_form(
    request: Request,
    viewer: ViewerContext = Depends(viewer_deps.require_staff),
):
    """
    An endpoint for displaying the homework form.

    Responses:
        - 200: HTML response with the homework form.
        - 401: Unauthorized.
        - 403: Wrong class.
    """
    class_id = viewer.class_id
    return templates.TemplateResponse(
        request=request,
        name="homework_form.html",
        context={"class_id": class_id, "homework": None},
    )


@router.post("/homework/new/", response_class=RedirectResponse)
async def post_homework_form(
    request: Request,
    form: Annotated[HomeworkForm, Form()],
    viewer: ViewerContext = Depends(viewer_deps.require_staff),
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for submitting a new homework form.

    Responses:
        - 303: Redirects to the homework list after submission.
        - 401: Unauthorized.
        - 403: Wrong session type.
    """

    staff_member = viewer.staff_member_verified
    class_id = staff_member.class_id

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
        class_id=class_id,
        subject=form.subject,
        title=form.title,
        description=form.description,
        date=form.date,
        images=image_paths,
        created_by=staff_member.username,
    )
    db_session.add(new_homework)
    db_session.commit()

    return RedirectResponse(url="/staff/dashboard/", status_code=303)


@router.get("/homework/{homework_id}/edit/", response_class=HTMLResponse)
async def get_edit_homework_form(
    request: Request,
    homework_id: int,
    viewer: ViewerContext = Depends(viewer_deps.require_staff),
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for displaying the homework form for editing.

    Responses:
        - 200: HTML response with the homework form.
        - 401: Unauthorized.
        - 403: Wrong session type.
    """

    homework = db_session.get(Homework, homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    if homework.class_id != viewer.staff_member_verified.class_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return templates.TemplateResponse(
        request=request,
        name="homework_form.html",
        context={"class_id": homework.class_id, "homework": homework},
    )


@router.post("/homework/{homework_id}/edit/")
async def post_edit_homework_form(
    request: Request,
    homework_id: int,
    form: Annotated[HomeworkForm, Form()],
    viewer: ViewerContext = Depends(viewer_deps.require_staff),
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for submitting an edited homework form.

    Responses:
        - 303: Redirects to the homework list after submission.
        - 401: Unauthorized.
        - 403: Wrong session type.
    """

    homework = db_session.get(Homework, homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    if homework.class_id != viewer.staff_member_verified.class_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    form_data = await request.form()
    raw_images = form_data.getlist("images")

    image_paths = []
    for img in raw_images:
        if not isinstance(img, str) and img.filename:
            ext = img.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join("uploads", filename)

            async with aiofiles.open(filepath, "wb") as f:
                content = await img.read()
                await f.write(content)

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

    return RedirectResponse(url="/staff/dashboard/", status_code=303)


@router.post("/homework/{homework_id}/delete")
async def delete_homework(
    homework_id: int,
    viewer: ViewerContext = Depends(viewer_deps.require_staff),
    db_session: Session = Depends(get_session),
):
    """
    An endpoint for deleting a homework.

    Responses:
        - 303: Redirects to the homework list after deletion.
        - 401: Unauthorized.
        - 403: Wrong session type.
    """

    homework = db_session.get(Homework, homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    staff_member = viewer.staff_member_verified
    if staff_member.class_id != homework.class_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_session.delete(homework)
    db_session.commit()

    return RedirectResponse(url="/staff/dashboard/", status_code=303)
