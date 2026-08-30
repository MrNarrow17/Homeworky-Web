from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.config import get_settings
from app.models.links import StaffClassLink
from app.schemas.class_ import ClassBase

if TYPE_CHECKING:
    from app.models.homework import Homework
    from app.models.staff import Staff


class Class(ClassBase, table=True):
    """
    Represents a class table in the database.

    Relationships:
        - Staff (moderators): One-to-many relationship.
        - Homework: One-to-many relationship.
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)
    hashed_password: str

    ### Relationships ###

    moderators: list["Staff"] = Relationship(
        back_populates="classes", link_model=StaffClassLink
    )

    homeworks: list["Homework"] = Relationship(
        back_populates="class_rel",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
        },
    )

    def __str__(self) -> str:
        return self.name
