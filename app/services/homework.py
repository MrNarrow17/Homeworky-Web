from collections.abc import Sequence
from datetime import date as date_type

from sqlmodel import Session, col, func, select

from app.models.homework import Homework


class HomeworkService:
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
            .where(Homework.class_id_db == class_id)
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
            .where(Homework.class_id_db == class_id)
            .where(Homework.date >= start_date)
            .where(Homework.date <= end_date)
            .order_by(col(Homework.date))
        )
        return db_session.exec(statement).all()

    @staticmethod
    def count_by_dates(
        db_session: Session,
        class_id: int,
        start_date: date_type,
        end_date: date_type,
    ) -> int:
        """
        Returns the number of homework items in the given class and date range.
        """

        statement = (
            select(func.count())
            .where(Homework.class_id_db == class_id)
            .where(Homework.date >= start_date)
            .where(Homework.date <= end_date)
        )
        return db_session.exec(statement).one()

    @staticmethod
    def count_in_class(db_session: Session, class_id: int) -> int:
        """
        Returns the number of homework items in the given class.
        """

        statement = select(func.count()).where(Homework.class_id_db == class_id)
        return db_session.exec(statement).one()
