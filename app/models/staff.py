from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.config import get_settings

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
    is_moderator: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)

    ### Foreign Keys ###

    class_id_db: int | None = Field(
        foreign_key="class.id",
        index=True,
        default=None,
        ondelete="CASCADE",
    )

    ### Relationships ###

    class_rel: "Class | None" = Relationship(back_populates="moderators")

    def __str__(self) -> str:
        return self.username
