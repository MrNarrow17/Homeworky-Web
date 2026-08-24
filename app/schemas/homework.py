from datetime import date as date_type

from sqlmodel import SQLModel


class HomeworkForm(SQLModel):
    """
    Schema for a homework form.
    """

    subject: str
    title: str
    description: str
    date: date_type
