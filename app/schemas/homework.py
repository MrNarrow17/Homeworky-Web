from datetime import date as date_type

from sqlmodel import SQLModel


class HomeworkForm(SQLModel):
    subject: str
    title: str
    description: str
    date: date_type
