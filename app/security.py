import hmac
import secrets
from abc import ABC, abstractmethod
from functools import lru_cache

import bcrypt
from fastapi import Depends, Request, Response
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select
from user_agents import parse

from app.config import Settings, get_settings
from app.database import get_session
from app.models.sessions import AppSession, AppSessionModel, ClassSession, StaffSession
from app.schemas.sessions import ViewerContext


class GeneralSecurity:
    """
    A class for general security operations.
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        token_secret = self._settings.token_secret
        if not token_secret:
            raise RuntimeError(
                "settings.token_secret is not configured. Add a long, random "
                "TOKEN_SECRET to your environment/config."
            )
        self._token_secret = token_secret.get_secret_value().encode("utf-8")

    ### Token Hashing ###

    def hash_token(self, opaque_token: str) -> str:
        """
        Hashes the given opaque token using the token secret with a sha256 hash.
        """

        return hmac.new(
            self._token_secret, opaque_token.encode("utf-8"), "sha256"
        ).hexdigest()

    ### Password Hashing ###

    def hash_password(self, plain_password: str) -> str:
        """
        Hashes the given plain password using bcrypt.
        """

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies the given plain password against the hashed password using bcrypt.
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False


class SessionSecurity(ABC, GeneralSecurity):
    """
    A base class for session security.
    """

    def __init__(
        self,
        settings: Settings | None = None,
    ):
        super().__init__(settings)

    ### Properties ###

    @property
    @abstractmethod
    def session_cookie(self) -> str:
        pass

    @property
    @abstractmethod
    def session_lifetime(self) -> int:
        pass

    @property
    @abstractmethod
    def session_model(self) -> AppSessionModel:
        pass

    ### User Agents ###

    def get_user_agent_from_request(self, request: Request) -> dict | None:
        """
        Gets the user agent string from a request then parses it to dict
        """
        user_agent_string = request.headers.get("user-agent")
        if user_agent_string:
            ua = parse(user_agent_string)
            return {
                "raw_user_agent": user_agent_string,
                "device_family": ua.device.family,
                "device_brand": ua.device.brand,
                "device_model": ua.device.model,
                "client_ip": request.client.host if request.client else None,
                "os_family": ua.os.family,
                "os_version": ua.os.version_string,
                "browser_family": ua.browser.family,
                "browser_version": ua.browser.version_string,
                "is_mobile": ua.is_mobile,
                "is_tablet": ua.is_tablet,
                "is_pc": ua.is_pc,
                "is_bot": ua.is_bot,
            }

    ### Sessions ###

    def _lookup_session(
        self, token_hash: str, db_session: Session
    ) -> AppSession | None:
        """
        Looks up a session by token hash in the database.
        """

        session_model = self.session_model
        stmt = select(session_model).where(session_model.token_hash == token_hash)
        return db_session.exec(stmt).first()

    def get_current_session(
        self, request: Request, db_session: Session
    ) -> AppSession | None:
        """
        Gets the current session from the request cookies and looks it up in the database.
        """

        token = request.cookies.get(self.session_cookie)
        if not token:
            return
        return self._lookup_session(self.hash_token(token), db_session)

    def issue_session(
        self,
        request: Request,
        response: Response,
        entity_id: int,
        db_session: Session,
    ) -> None:
        """
        Issues a new session for the given entity and sets the session cookie.
        """

        raw_token = secrets.token_urlsafe(64)
        token_hash = self.hash_token(raw_token)

        new_session = self.session_model.from_entity(
            token_hash, entity_id, device_data=self.get_user_agent_from_request(request)
        )
        db_session.add(new_session)
        db_session.commit()

        self.set_session_cookie(response, raw_token)

    def invalidate_session(
        self,
        request: Request,
        response: Response,
        db_session: Session,
    ) -> None:
        """
        Invalidates the current session by deleting it from the database and clearing the session cookie.
        """

        token = request.cookies.get(self.session_cookie)
        if token:
            existing_session = self._lookup_session(self.hash_token(token), db_session)

            if existing_session:
                db_session.delete(existing_session)
                db_session.commit()

        self.delete_session_cookie(response)

    ### Cookies ###

    def set_session_cookie(self, response: Response, token: str) -> Response:
        """
        Sets the session cookie in the response with the given token.
        """

        response.set_cookie(
            key=self.session_cookie,
            value=token,
            httponly=True,
            max_age=self.session_lifetime,
            samesite="lax",
            secure=not self._settings.debug_mode,
            path="/",
        )
        return response

    def delete_session_cookie(self, response: Response) -> Response:
        """
        Deletes the session cookie from the response.
        """

        response.delete_cookie(
            key=self.session_cookie,
            httponly=True,
            samesite="lax",
            secure=not self._settings.debug_mode,
            path="/",
        )
        return response


class ClassSessionSecurity(SessionSecurity):
    """
    A class for specifying properties of ClassSession security.
    """

    @property
    def session_cookie(self) -> str:
        return self._settings.class_session_cookie

    @property
    def session_lifetime(self) -> int:
        return self._settings.class_session_lifetime

    @property
    def session_model(self) -> AppSessionModel:
        return ClassSession


class StaffSessionSecurity(SessionSecurity):
    """
    A class for specifying properties of StaffSession security.
    """

    @property
    def session_cookie(self) -> str:
        return self._settings.staff_session_cookie

    @property
    def session_lifetime(self) -> int:
        return self._settings.staff_session_lifetime

    @property
    def session_model(self) -> AppSessionModel:
        return StaffSession


class ViewerSecurity:
    """
    Resolves the current viewer across all registered session types
    and enforces coarse authorization (class-level vs staff-level).
    """

    def __init__(self, *securities: SessionSecurity):
        self._securities = securities

    def get_current_session(
        self, request: Request, db_session: Session
    ) -> AppSession | None:
        """
        Iterates through all registered securities and returns the first valid session.
        """

        for sec in self._securities:
            session = sec.get_current_session(request, db_session)
            if session is not None:
                return session
        return None

    def get_view_context(
        self,
        request: Request,
        db_session: Session,
    ) -> ViewerContext | None:
        """
        Returns the viewer context for the current session, if one exists.
        """

        session = self.get_current_session(request, db_session)
        return ViewerContext.from_session(session) if session is not None else None

    def require_session(
        self,
        request: Request,
        db_session: Session,
        *,
        class_id: int | None = None,
        staff_required: bool = False,
    ) -> ViewerContext:
        """
        Requires a session to be present and valid.
        """

        session = self.get_current_session(request, db_session)
        if session is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if staff_required and not session.is_staff:
            raise HTTPException(status_code=403, detail="Staff required")
        if class_id is not None and session.class_id != class_id:
            raise HTTPException(status_code=403, detail="Wrong class")
        return ViewerContext.from_session(session)


class ViewerSecurityDependencies:
    """
    A collection of dependencies for the ViewerSecurity object.
    """

    def __init__(self, viewer_security: ViewerSecurity):
        self._viewer_security = viewer_security

    def get_viewer_context(
        self,
        request: Request,
        db_session: Session = Depends(get_session),
    ) -> ViewerContext | None:
        """Get the viewer context for the given request and session"""
        return self._viewer_security.get_view_context(request, db_session)

    def require_any(
        self, request: Request, db_session: Session = Depends(get_session)
    ) -> ViewerContext:
        """Any valid session required"""
        return self._viewer_security.require_session(request, db_session)

    def require_class_any(
        self,
        request: Request,
        class_id: int,
        db_session: Session = Depends(get_session),
    ) -> ViewerContext:
        """Any valid session required but additionally verified against the class_id"""
        return self._viewer_security.require_session(
            request, db_session, class_id=class_id
        )

    def require_staff(
        self, request: Request, db_session: Session = Depends(get_session)
    ) -> ViewerContext:
        """Staff session required."""
        return self._viewer_security.require_session(
            request, db_session, staff_required=True
        )

    def require_class_staff(
        self,
        request: Request,
        class_id: int,
        db_session: Session = Depends(get_session),
    ) -> ViewerContext:
        """Staff session required but additionally verified against the class_id"""
        return self._viewer_security.require_session(
            request, db_session, class_id=class_id, staff_required=True
        )


@lru_cache
def get_general_security() -> GeneralSecurity:
    """
    A cached factory function for the GeneralSecurity object.
    """

    return GeneralSecurity()


@lru_cache
def get_staff_security() -> StaffSessionSecurity:
    """
    A cached factory function for the StaffSessionSecurity object.
    """
    return StaffSessionSecurity()


@lru_cache
def get_class_security() -> ClassSessionSecurity:
    """
    A cached factory function for the ClassSessionSecurity object.
    """
    return ClassSessionSecurity()


@lru_cache
def get_viewer_security() -> ViewerSecurity:
    """
    A cached factory function for the ViewerSecurity object.
    """

    return ViewerSecurity(StaffSessionSecurity(), ClassSessionSecurity())


@lru_cache
def get_viewer_dependencies() -> ViewerSecurityDependencies:
    """
    A cached factory function for the ViewerSecurityDependencies object.
    """
    return ViewerSecurityDependencies(get_viewer_security())
