from sqlmodel import SQLModel


class AppSession(SQLModel):
    """
    Represents a user session in the application.
    """

    session_id: int
    staff_id: int | None = None
    class_id: int | None = None
    is_admin: bool = False
    is_mod: bool = False

    ip_address: str | None = None
    user_agent: dict | None = None

    @property
    def is_staff(self) -> bool:
        return self.is_admin or self.is_mod
