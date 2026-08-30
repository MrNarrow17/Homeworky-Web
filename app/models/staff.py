from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.config import get_settings
from app.models.links import StaffClassLink

if TYPE_CHECKING:
    from app.models.class_ import Class


class Staff(SQLModel, table=True):
    """
    Represents a staff table in the database.

    Relationships:
        - Class: Many-to-one relationship.
    """

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str

    is_admin: bool = Field(default=False)
    is_mod: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)

    ### Relationships ###

    classes: list["Class"] = Relationship(
        back_populates="moderators", link_model=StaffClassLink
    )

    def __str__(self) -> str:
        return self.username
