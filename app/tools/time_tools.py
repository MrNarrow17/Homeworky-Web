from datetime import date as date_type
from datetime import timedelta

from fastapi.exceptions import HTTPException

from app.config import get_settings

settings = get_settings()


def get_week_range(
    year: int, week: int, day: date_type | None = None
) -> tuple[date_type, date_type]:
    """
    Returns the start and end dates of a given week in a given year.
    """
    if day is not None:
        return day, day
    try:
        start_date = date_type.fromisocalendar(year, week, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid year or week number")

    end_date = start_date + timedelta(days=6)
    return start_date, end_date


def resolve_date_parameters(
    year: int | None = None,
    week: int | None = None,
    day: date_type | None = None,
) -> tuple[int, int, date_type | None]:
    """
    Returns selected_year, selected_week, and selected_day aligned to the same timeframe.
    """
    now = settings.local_time
    iso_year, iso_week, _ = now.isocalendar()

    if day is not None:
        day_year, day_week, _ = day.isocalendar()
        return day_year, day_week, day

    selected_year = year if year is not None else iso_year
    selected_week = week if week is not None else (iso_week if year is None else 1)

    return selected_year, selected_week, None
