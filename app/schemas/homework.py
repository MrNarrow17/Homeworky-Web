from datetime import date as date_type

from pydantic import ConfigDict
from sqlmodel import SQLModel


class HomeworkForm(SQLModel):
    """
    Schema for a homework form.
    """

    model_config = ConfigDict(str_strip_whitespace=True)  # type: ignore

    subject: str
    title: str
    description: str
    date: date_type
