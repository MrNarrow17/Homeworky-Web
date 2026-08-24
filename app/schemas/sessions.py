from dataclasses import dataclass, field

from app.models.sessions import SessionType


@dataclass(frozen=True)
class ViewerContext:
    """
    Represents the context of the viewer.
    """

    class_id: int
    session_type: SessionType

    is_staff: bool = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "is_staff", self.session_type == SessionType.STAFF)
