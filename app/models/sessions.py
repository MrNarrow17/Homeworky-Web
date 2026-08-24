from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.staff import StaffMember

type AppSession = StaffSession | ClassSession
type AppSessionModel = type[AppSession]

settings = get_settings()


class ClassSession(SQLModel, table=True):
    """
    Represents a class session table in the database.

    Relationships:
        - Class: Many-to-one relationship.
    """

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    token_hash: str = Field(index=True)

    class_: Class = Relationship(back_populates="sessions")
    class_id: int = Field(
        default=None, foreign_key="class.id", ondelete="CASCADE", index=True
    )

    @classmethod
    def from_entity(cls, token_hash: str, entity_id: int) -> ClassSession:
        """
        Creates a ClassSession from an entity ID. Used for a polymorphic relationship
        """
        return cls(token_hash=token_hash, class_id=entity_id)

    @property
    def session_type(self) -> SessionType:
        """
        Returns the session type for this session. Used for polymorphic relationship.
        """
        return SessionType.CLASS

    def __str__(self) -> str:
        """
        Represents the string version of the ClassSession model.
        """
        return f"Session #{self.id}"


class StaffSession(SQLModel, table=True):
    """
    Represents a staff session table in the database.

    Relationships:
        - StaffMember: Many-to-one relationship.
    """

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    token_hash: str = Field(index=True)

    staff_member: StaffMember = Relationship(back_populates="sessions")
    staff_member_id: int = Field(
        default=None, foreign_key="staffmember.id", ondelete="CASCADE", index=True
    )

    @classmethod
    def from_entity(cls, token_hash: str, entity_id: int) -> StaffSession:
        """
        Creates a ClassSession from an entity ID. Used for a polymorphic relationship
        """
        return cls(token_hash=token_hash, staff_member_id=entity_id)

    @property
    def class_(self) -> Class:
        """
        Returns the class associated with this staff session.
        """
        return self.staff_member.class_

    @property
    def class_id(self) -> int:
        """
        Returns the class ID associated with this staff session.
        """
        return self.staff_member.class_id

    @property
    def session_type(self) -> SessionType:
        """
        Returns the session type for this session. Used for polymorphic relationship.
        """
        return SessionType.STAFF

    def __str__(self) -> str:
        """
        Represents the string version of the StaffSession model.
        """
        return f"Session #{self.id}"


class SessionType(Enum):
    STAFF = (StaffSession, settings.staff_session_lifetime)
    CLASS = (ClassSession, settings.class_session_lifetime)

    def __init__(self, session_model: AppSessionModel, lifetime: int) -> None:
        self._session_model = session_model
        self._lifetime = lifetime

    @property
    def session_model(self) -> AppSessionModel:
        return self._session_model

    @property
    def lifetime(self) -> int:
        return self._lifetime
