from sqlmodel import Field, SQLModel


class ClassBase(SQLModel):
    """
    Base schema for a class model.
    """

    name: str = Field(index=True)


class ClassJoin(SQLModel):
    """
    Schema for a class join form.
    """

    id: int
    password: str


class ClassPublic(ClassBase):
    """
    Public view of a class model.
    """

    id: int
