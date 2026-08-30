from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from app.database import get_session
from app.models.homework import Homework
from app.schemas.sessions import AppSession
from app.security.redis import RedisSessionManager, get_session_manager


class ViewerDependencies:
    """
    FastAPI dependency methods for resolving and authorizing the current viewer.
    """

    def __init__(self, session_manager: RedisSessionManager | None = None):
        self._session_manager = session_manager or get_session_manager()

    @property
    def session_manager(self) -> RedisSessionManager:
        """
        Returns the session manager.
        """

        return self._session_manager

    def get_viewer(self, request: Request) -> AppSession:
        """
        Returns the current session, or an unauthenticated null-object AppSession.
        """

        return self._session_manager.get_session(request)

    def require_any(self, request: Request) -> AppSession:
        """
        Requires any valid session (staff or class).
        """

        session = self.get_viewer(request)
        if not session.is_authenticated:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
        return session

    def require_staff(self, request: Request) -> AppSession:
        """
        Requires a staff (or admin) session.
        """

        session = self.require_any(request)
        if not session.is_staff:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Staff required")
        return session

    def require_admin(self, request: Request) -> AppSession:
        """
        Requires an admin session.
        """

        session = self.require_any(request)
        if not session.is_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin required")
        return session

    def require_class_any(self, class_id: int, request: Request) -> AppSession:
        """
        Requires a session (staff or class) authorized to view the given class.
        """

        session = self.require_any(request)
        if not session.can_view_class(class_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Wrong class")
        return session

    def require_class_staff(self, request: Request, class_id: int) -> int:
        """
        Requires a staff session authorized to view the given class.
        """

        viewer = self.require_staff(request)
        if not viewer.can_view_class(class_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Wrong class")
        return class_id

    def require_homework_staff(
        self,
        request: Request,
        homework_id: int,
        db_session: Session = Depends(get_session),
    ) -> Homework:
        """
        Requires a staff session authorized to view the given homework.
        """

        viewer = self.require_staff(request)
        homework = db_session.get(Homework, homework_id)
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        if not viewer.can_view_class(homework.class_id_db):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
        return homework


def get_viewer_dependencies(
    session_manager: RedisSessionManager | None = None,
) -> ViewerDependencies:
    """
    Factory function for a ViewerDependencies object.
    """
    return ViewerDependencies(session_manager)
