from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.sessions import StaffSession


class StaffMember(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)
    hashed_password: str

    class_: "Class" = Relationship(back_populates="staff")
    class_id: int = Field(
        foreign_key="class.id",
        ondelete="CASCADE",
    )

    sessions: list["StaffSession"] = Relationship(back_populates="staff_member")
