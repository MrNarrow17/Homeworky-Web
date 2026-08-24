from dataclasses import dataclass

from app.models.class_ import Class
from app.models.sessions import AppSession
from app.models.staff import StaffMember


@dataclass(frozen=True)
class ViewerContext:
    """
    Represents the context of the viewer.
    """

    session: AppSession

    @classmethod
    def from_session(cls, session: AppSession) -> "ViewerContext":
        return cls(session=session)

    @property
    def class_(self) -> Class:
        return self.session.class_

    @property
    def class_id(self) -> int:
        return self.session.class_id

    @property
    def staff_member(self) -> StaffMember | None:
        return self.session.staff_member

    @property
    def staff_member_verified(self) -> StaffMember:
        if self.staff_member is None:
            raise RuntimeError("Staff accessed on a non-staff viewer context")
        return self.staff_member

    @property
    def staff_member_id(self) -> int | None:
        return self.session.staff_member_id

    @property
    def is_staff(self) -> bool:
        return self.session.is_staff
