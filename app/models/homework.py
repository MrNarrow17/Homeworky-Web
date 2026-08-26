from collections.abc import Sequence
from datetime import date as date_type
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import JSON, Field, Relationship, Session, SQLModel, col, func, select

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

    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)
    created_by: str

    class_: "Class" = Relationship(back_populates="homeworks")
    class_id: int = Field(foreign_key="class.id", ondelete="CASCADE", index=True)

    @staticmethod
    def get_in_class(
        db_session: Session,
        class_id: int,
    ) -> Sequence["Homework"]:
        """
        Returns a list of homework items in the given class.
        """

        statement = (
            select(Homework)
            .where(Homework.class_id == class_id)
            .order_by(col(Homework.date))
        )
        return db_session.exec(statement).all()

    @staticmethod
    def get_by_dates(
        db_session: Session,
        class_id: int,
        start_date: date_type,
        end_date: date_type,
    ) -> Sequence["Homework"]:
        """
        Returns a list of homework items for the given class and date range.
        """

        statement = (
            select(Homework)
            .where(Homework.class_id == class_id)
            .where(Homework.date >= start_date)
            .where(Homework.date <= end_date)
            .order_by(col(Homework.date))
        )
        return db_session.exec(statement).all()

    @classmethod
    def count_by_dates(
        cls,
        db_session: Session,
        class_id: int,
        start_date: date_type,
        end_date: date_type,
    ) -> int:
        """
        Returns the number of homework items in the given class and date range.
        """

        return len(cls.get_by_dates(db_session, class_id, start_date, end_date))

    @staticmethod
    def count_in_class(db_session: Session, class_id: int) -> int:
        """
        Returns the number of homework items in the given class.
        """

        statement = select(func.count()).where(Homework.class_id == class_id)
        return db_session.exec(statement).one()

    def __str__(self) -> str:
        """
        Represents the string version of the homework model.
        """

        return f"Homework #{self.id}"
