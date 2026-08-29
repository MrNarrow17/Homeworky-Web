from app.schemas.sessions import AppSession


class Viewer:
    """
    A class representing a viewer.
    """

    def __init__(self, session: AppSession | None = None) -> None:
        self._session = session

    @property
    def is_authenticated(self) -> bool:
        """Return whether the viewer is authenticated."""
        return bool(self._session)

    @property
    def class_id(self) -> int | None:
        """Return the class ID of the viewer, or None if not applicable."""
        return self._session.class_id if self._session else None

    def can_view_class(self, class_id: int) -> bool:
        """Returns whether the viewer can view the given class."""
        return (
            self._session.class_id == class_id or self._session.is_admin
            if self._session
            else False
        )

    def can_view_mod_pages(self) -> bool:
        """Returns whether the viewer can view the mod explicit pages."""
        return self._session.is_staff if self._session else False

    def can_view_admin_pages(self) -> bool:
        """Returns whether the viewer can view the admin explicit pages."""
        return self._session.is_admin if self._session else False
