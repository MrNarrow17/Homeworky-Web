from datetime import datetime
from typing import TYPE_CHECKING, Self

from sqlmodel import Field, Relationship, SQLModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.staff import Staff


class AppSession(SQLModel, table=True):
    """
    Represents a base app session model.
    """

    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(index=True, unique=True)

    created_at: datetime = Field(default_factory=lambda: get_settings().current_time)

    ### Foreign Keys ###

    staff_id_db: int | None = Field(
        foreign_key="staff.id",
        default=None,
        ondelete="CASCADE",
        index=True,
    )

    class_id_db: int | None = Field(
        foreign_key="class.id",
        default=None,
        ondelete="CASCADE",
        index=True,
    )

    ### Relationships ###

    staff_rel: "Staff | None" = Relationship(back_populates="sessions")
    class_rel: "Class | None" = Relationship(back_populates="sessions")

    ### User Agent Data ###

    raw_user_agent: str | None = Field(default=None, index=True)

    device_family: str | None = Field(default=None, index=True)
    device_brand: str | None = Field(default=None)
    device_model: str | None = Field(default=None)

    client_ip: str | None = Field(default=None)

    os_family: str | None = Field(default=None, index=True)
    os_version: str | None = Field(default=None)

    browser_family: str | None = Field(default=None, index=True)
    browser_version: str | None = Field(default=None)

    is_mobile: bool = Field(default=False)
    is_tablet: bool = Field(default=False)
    is_pc: bool = Field(default=False)
    is_bot: bool = Field(default=False)

    ### Factory Methods ###

    @classmethod
    def from_staff(
        cls, token_hash: str, staff_id: int, device_data: dict | None = None
    ) -> Self:
        payload = {"token_hash": token_hash, "staff_id_db": staff_id}
        if device_data:
            payload.update(device_data)
        return cls(**payload)

    @classmethod
    def from_class(
        cls, token_hash: str, class_id: int, device_data: dict | None = None
    ) -> Self:
        payload = {"token_hash": token_hash, "class_id_db": class_id}
        if device_data:
            payload.update(device_data)
        return cls(**payload)

    ### Properties ###

    @property
    def is_staff_session(self) -> bool:
        return self.staff_id_db is not None

    @property
    def is_class_session(self) -> bool:
        return self.class_id_db is not None

    def __str__(self) -> str:
        return f"Session #{self.id}"
