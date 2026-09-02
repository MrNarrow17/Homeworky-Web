from collections.abc import Sequence
from datetime import date as date_type

from fastapi import Request
from sqlmodel import Session, col, func, select
from user_agents import parse

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

        print(
            f"get_by_dates: class_id={class_id}, start_date={start_date}, end_date={end_date}"
        )

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


class SessionService:
    @staticmethod
    def get_user_agent_from_request(request: Request) -> dict | None:
        """
        Gets the user agent string from a request then parses it to dict
        """
        user_agent_string = request.headers.get("user-agent")
        if user_agent_string:
            ua = parse(user_agent_string)
            return {
                "raw_user_agent": user_agent_string,
                "device_family": ua.device.family,
                "device_brand": ua.device.brand,
                "device_model": ua.device.model,
                "client_ip": request.client.host if request.client else None,
                "os_family": ua.os.family,
                "os_version": ua.os.version_string,
                "browser_family": ua.browser.family,
                "browser_version": ua.browser.version_string,
                "is_mobile": ua.is_mobile,
                "is_tablet": ua.is_tablet,
                "is_pc": ua.is_pc,
                "is_bot": ua.is_bot,
            }
