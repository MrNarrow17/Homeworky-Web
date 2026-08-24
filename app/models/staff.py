from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.sessions import StaffSession


class StaffMember(SQLModel, table=True):
    """
    Represents a staff member table in the database.

    Relationships:
        - Class: Many-to-one relationship.
        - StaffSession: One-to-many relationship.
    """

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)
    hashed_password: str

    class_: "Class" = Relationship(back_populates="staff")
    class_id: int = Field(
        foreign_key="class.id",
        ondelete="CASCADE",
    )

    sessions: list["StaffSession"] = Relationship(
        back_populates="staff_member",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
        },
    )

    def __str__(self) -> str:
        """
        Represents the string version of the StaffMember model.
        """
        return self.username
