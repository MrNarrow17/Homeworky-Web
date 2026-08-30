from sqlmodel import Field, SQLModel


class StaffClassLink(SQLModel, table=True):
    """
    Link table between Staff and Class.
    """

    staff_id: int | None = Field(
        default=None,
        foreign_key="staff.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    class_id: int | None = Field(
        default=None,
        foreign_key="class.id",
        primary_key=True,
        index=True,
        ondelete="CASCADE",
    )
