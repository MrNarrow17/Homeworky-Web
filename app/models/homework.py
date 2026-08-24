from datetime import date as date_type
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import JSON, Field, Relationship, SQLModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.models.class_ import Class


class Homework(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    date: date_type

    subject: str
    title: str
    description: str
    images: list[str] = Field(default_factory=list, sa_type=JSON)

    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)
    created_by: str

    class_: "Class" = Relationship(back_populates="homeworks")
    class_id: int = Field(foreign_key="class.id", ondelete="CASCADE", index=True)
