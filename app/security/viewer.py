from abc import ABC, abstractmethod

from app.models.sessions import AppSession


class Viewer(ABC):
    """Capability-based authorization interface."""

    @property
    @abstractmethod
    def class_id(self) -> int | None:
        """
        Return the class ID of the viewer, or None if not applicable.
        """

    @abstractmethod
    def can_view_class(self, class_id: int) -> bool:
        """Returns whether the viewer can view the given class."""

    @abstractmethod
    def can_view_mod_pages(self) -> bool:
        """Returns whether the viewer can view the mod explicit pages."""

    @abstractmethod
    def can_view_admin_pages(self) -> bool:
        """Returns whether the viewer can view the admin explicit pages."""


class ClassViewer(Viewer):
    def __init__(self, session: AppSession):
        self._session = session

    @property
    def class_id(self) -> int | None:
        return self._session.class_id_db

    def can_view_class(self, class_id: int) -> bool:
        return self._session.class_id_db == class_id

    def can_view_mod_pages(self) -> bool:
        return False

    def can_view_admin_pages(self) -> bool:
        return False


class ModViewer(Viewer):
    def __init__(self, session: AppSession):
        self._session = session

    @property
    def class_id(self) -> int | None:
        if not self._session.staff_rel:
            return None
        return self._session.staff_rel.class_id_db

    def can_view_class(self, class_id: int) -> bool:
        if not self._session.staff_rel:
            return False
        return self._session.staff_rel.class_id_db == class_id

    def can_view_mod_pages(self) -> bool:
        return True

    def can_view_admin_pages(self) -> bool:
        return False


class AdminViewer(Viewer):
    def __init__(self, session: AppSession):
        self._session = session

    @property
    def class_id(self) -> int | None:
        return None

    def can_view_class(self, class_id: int) -> bool:
        return True

    def can_view_mod_pages(self) -> bool:
        return True

    def can_view_admin_pages(self) -> bool:
        return True
