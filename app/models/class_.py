from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.config import get_settings
from app.schemas.class_ import ClassBase

if TYPE_CHECKING:
    from app.models.homework import Homework
    from app.models.sessions import ClassSession
    from app.models.staff import StaffMember


class Class(ClassBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)
    hashed_password: str

    staff: list["StaffMember"] = Relationship(
        back_populates="class_",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
    homeworks: list["Homework"] = Relationship(
        back_populates="class_",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
    sessions: list["ClassSession"] = Relationship(
        back_populates="class_",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )

    def __str__(self):
        return self.name
