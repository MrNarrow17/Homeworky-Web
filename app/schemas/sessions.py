from typing import TYPE_CHECKING, Self

from fastapi import Request
from sqlmodel import SQLModel

from app.config import get_settings
from app.services import SessionService

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.staff import Staff

settings = get_settings()


class AppSession(SQLModel):
    """
    Represents a user session in the application.
    """

    staff_id: int | None = None
    staff_class_ids: list[int] = []
    class_id: int | None = None
    lifetime: int = 0
    is_admin: bool = False
    is_mod: bool = False

    ip_address: str | None = None
    user_agent: dict | None = None

    @classmethod
    def from_raw_data(cls, data: bytes | str | None) -> Self:
        if data is None:
            return cls()
        return cls.model_validate_json(data)

    @classmethod
    def from_class(cls, request: Request, class_: "Class") -> Self:
        return cls(
            class_id=class_.id,
            lifetime=settings.class_session_lifetime,
            ip_address=request.client.host if request.client else None,
            user_agent=SessionService.get_user_agent_from_request(request),
        )

    @classmethod
    def from_staff(cls, request: Request, staff: "Staff") -> Self:
        return cls(
            staff_id=staff.id,
            staff_class_ids=[c.id for c in staff.classes],
            lifetime=settings.staff_session_lifetime,
            is_admin=staff.is_admin,
            is_mod=staff.is_mod,
            ip_address=request.client.host if request.client else None,
            user_agent=SessionService.get_user_agent_from_request(request),
        )

    @property
    def is_authenticated(self) -> bool:
        """Return whether the viewer is authenticated."""
        return bool((self.staff_id or self.class_id) and self.lifetime > 0)

    def can_view_class(self, class_id: int) -> bool:
        """Returns whether the viewer can view the given class."""
        return (
            self.class_id == class_id
            or class_id in self.staff_class_ids
            or self.is_admin
            if self.is_authenticated
            else False
        )

    def can_view_mod_pages(self) -> bool:
        """Returns whether the viewer can view the mod explicit pages."""
        return self.is_staff if self.is_authenticated else False

    def can_view_admin_pages(self) -> bool:
        """Returns whether the viewer can view the admin explicit pages."""
        return self.is_admin if self.is_authenticated else False

    @property
    def is_staff(self) -> bool:
        return self.is_admin or self.is_mod
