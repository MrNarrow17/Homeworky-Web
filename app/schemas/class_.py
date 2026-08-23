from sqlmodel import Field, SQLModel


class ClassBase(SQLModel):
    name: str = Field(index=True)


class ClassJoin(SQLModel):
    id: int
    password: str


class ClassPublic(ClassBase):
    id: int
