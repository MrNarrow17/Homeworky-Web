import wtforms
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend

from app.config import get_settings
from app.models.class_ import Class
from app.models.staff import StaffMember
from app.security import get_general_security

settings = get_settings()
security = get_general_security()


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool | RedirectResponse:
        form = await request.form()
        username, password = form["username"], form["password"]

        if username != settings.admin_username or password != settings.admin_password:
            return False

        request.session.update({"token": settings.token_secret})

        return True

    async def logout(self, request: Request) -> bool | RedirectResponse:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        return bool(token)


class ClassAdmin(ModelView, model=Class):
    name = "Class"
    name_plural = "Classes"

    column_list = [Class.id, Class.name, Class.created_at]

    form_columns = [Class.name, Class.hashed_password]

    form_overrides = {
        Class.hashed_password: wtforms.PasswordField,
    }

    form_args = {
        "hashed_password": {
            "label": "Password",
        }
    }

    async def on_model_change(
        self, data: dict, model: Class, is_created: bool, request: Request
    ) -> None:
        raw_password = data.get("hashed_password")
        if raw_password:
            secure_hash = security.hash_password(raw_password)
            data["hashed_password"] = secure_hash
            model.hashed_password = secure_hash

        elif not is_created:
            data["hashed_password"] = model.hashed_password


class StaffAdmin(ModelView, model=StaffMember):
    name = "Staff"
    name_plural = "Staff"

    column_list = [
        StaffMember.id,
        StaffMember.username,
        StaffMember.class_,
        StaffMember.created_at,
    ]

    form_columns = [
        StaffMember.username,
        StaffMember.class_,
        StaffMember.hashed_password,
    ]

    form_overrides = {
        Class.hashed_password: wtforms.PasswordField,
    }

    form_args = {
        "hashed_password": {
            "label": "Password",
        }
    }

    async def on_model_change(
        self, data: dict, model: Class, is_created: bool, request: Request
    ) -> None:
        raw_password = data.get("hashed_password")
        if raw_password:
            secure_hash = security.hash_password(raw_password)
            data["hashed_password"] = secure_hash
            model.hashed_password = secure_hash

        elif not is_created:
            data["hashed_password"] = model.hashed_password
