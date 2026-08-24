from datetime import date, timedelta


def get_week_range(year: int, week: int) -> tuple[date, date]:
    """
    Returns the start and end dates of a given week in a given year.
    """

    first_day_of_year = date(year, 1, 4)
    start_of_first_week = first_day_of_year - timedelta(
        days=first_day_of_year.isoweekday() - 1
    )

    start_date = start_of_first_week + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start_date, end_date
