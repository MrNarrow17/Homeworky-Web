from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.staff import StaffMember

type AppSession = StaffSession | ClassSession
type AppSessionModel = type[AppSession]

settings = get_settings()


class BaseAppSession(SQLModel):
    """
    Represents a base app session model.
    """

    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(index=True)


class ClassSession(BaseAppSession, table=True):
    """
    Represents a class session table in the database.

    Relationships:
        - Class: Many-to-one relationship.
    """

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
    def is_staff(self) -> bool:
        """
        Returns whether the session is a staff session.
        """
        return False

    @property
    def staff_member(self) -> StaffMember | None:
        """
        Returns the staff member associated with this session, if any.
        """
        return None

    @property
    def staff_member_id(self) -> int | None:
        """
        Returns the ID of the staff member associated with this session, if any.
        """
        return None

    def __str__(self) -> str:
        """
        Represents the string version of the ClassSession model.
        """
        return f"Session #{self.id}"


class StaffSession(BaseAppSession, table=True):
    """
    Represents a staff session table in the database.

    Relationships:
        - StaffMember: Many-to-one relationship.
    """

    staff_member: StaffMember = Relationship(back_populates="sessions")
    staff_member_id: int = Field(
        default=None, foreign_key="staffmember.id", ondelete="CASCADE", index=True
    )

    @classmethod
    def from_entity(cls, token_hash: str, entity_id: int) -> StaffSession:
        """
        Creates a StaffSession from an entity ID. Used for a polymorphic relationship
        """
        return cls(token_hash=token_hash, staff_member_id=entity_id)

    @property
    def is_staff(self) -> bool:
        """
        Returns whether the session is a staff session.
        """
        return True

    @property
    def class_(self) -> Class:
        """
        Returns the class of the staff member.
        """
        return self.staff_member.class_

    @property
    def class_id(self) -> int:
        """
        Returns the class ID of the staff member.
        """
        return self.staff_member.class_id

    def __str__(self) -> str:
        """
        Represents the string version of the StaffSession model.
        """
        return f"Session #{self.id}"
