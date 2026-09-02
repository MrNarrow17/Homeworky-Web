from datetime import date as date_type
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import JSON, Column, DateTime, Field, Relationship, SQLModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.models.class_ import Class


class Homework(SQLModel, table=True):
    """
    Represents a homework table in the database.

    Relationships:
        - Class: Many-to-one relationship.
    """

    id: int | None = Field(default=None, primary_key=True)

    date: date_type

    subject: str
    title: str
    description: str
    images: list[str] = Field(default_factory=list, sa_type=JSON)

    created_at: datetime = Field(
        default_factory=lambda: get_settings().utc_time,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_by: str

    class_rel: "Class" = Relationship(back_populates="homeworks")
    class_id_db: int = Field(foreign_key="class.id", ondelete="CASCADE", index=True)

    @property
    def local_created_at(self) -> datetime:
        return self.created_at.astimezone(get_settings().local_timezone)

    def __str__(self) -> str:
        return f"Homework #{self.id}"
