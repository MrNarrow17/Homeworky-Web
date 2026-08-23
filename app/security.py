import hmac
import secrets
from functools import lru_cache

import bcrypt
from fastapi import Depends, Request, Response
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select

from app.config import Settings, get_settings
from app.database import get_session
from app.models.sessions import AppSession, ClassSession, StaffSession
from app.schemas.sessions import SessionType, ViewerContext


class GeneralSecurity:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        token_secret = self._settings.token_secret
        if not token_secret:
            raise RuntimeError(
                "settings.token_secret is not configured. Add a long, random "
                "TOKEN_SECRET to your environment/config."
            )
        self._token_secret = token_secret.encode("utf-8")

    ### Token Hashing ###

    def hash_token(self, opaque_token: str) -> str:
        return hmac.new(
            self._token_secret, opaque_token.encode("utf-8"), "sha256"
        ).hexdigest()

    ### Password Hashing ###

    def hash_password(self, plain_password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False


class SessionSecurity(GeneralSecurity):
    def __init__(
        self,
        settings: Settings | None = None,
    ):
        super().__init__(settings)
        self._session_cookie = self._settings.session_cookie

    ### Sessions ###

    def _lookup_session(
        self, token_hash: str, db_session: Session
    ) -> AppSession | None:
        class_stmt = select(ClassSession).where(ClassSession.token_hash == token_hash)
        class_session = db_session.exec(class_stmt).first()
        if class_session:
            return class_session

        staff_stmt = select(StaffSession).where(StaffSession.token_hash == token_hash)
        staff_session = db_session.exec(staff_stmt).first()
        if staff_session:
            return staff_session

        return None

    def get_current_session(
        self, request: Request, db_session: Session
    ) -> AppSession | None:
        token = request.cookies.get(self._session_cookie)
        if not token:
            return
        return self._lookup_session(token, db_session)

    def issue_session(
        self,
        response: Response,
        session_type: SessionType,
        entity_id: int,
        db_session: Session,
    ) -> None:
        token_hash = self.hash_token(secrets.token_urlsafe(64))
        new_session = session_type.session_model.from_entity(token_hash, entity_id)
        db_session.add(new_session)
        db_session.commit()

        self.set_session_cookie(response, token_hash, session_type)

    def invalidate_session(
        self,
        request: Request,
        response: Response,
        db_session: Session,
    ) -> None:
        token = request.cookies.get(self._session_cookie)
        if not token:
            return

        existing_session = self._lookup_session(token, db_session)

        if existing_session:
            db_session.delete(existing_session)
            db_session.commit()

            self.delete_session_cookie(response)

    ### Cookies ###

    def set_session_cookie(
        self, response: Response, token: str, session_type: SessionType
    ) -> Response:
        response.set_cookie(
            key=self._session_cookie,
            value=token,
            httponly=True,
            max_age=session_type.lifetime,
            samesite="lax",
            secure=not self._settings.debug_mode,
        )
        return response

    def delete_session_cookie(self, response: Response) -> Response:
        response.delete_cookie(
            key=self._session_cookie,
            httponly=True,
            samesite="lax",
            secure=not self._settings.debug_mode,
        )
        return response


class ClassSecurity(SessionSecurity):
    def __init__(
        self,
        settings: Settings | None = None,
    ):
        super().__init__(settings)

    def get_view_context(
        self,
        request: Request,
        db_session: Session = Depends(get_session),
    ) -> ViewerContext | None:
        session = self.get_current_session(request, db_session)
        if session:
            return ViewerContext(session.class_id, session.session_type)

    def require_session(
        self,
        request: Request,
        class_id: int,
        db_session: Session = Depends(get_session),
    ) -> ViewerContext:
        session = self.get_current_session(request, db_session)
        if session:
            if session.class_id != class_id:
                raise HTTPException(status_code=403, detail="Wrong class")
            return ViewerContext(class_id, session.session_type)
        raise HTTPException(status_code=401, detail="Unauthorized")


class StaffSecurity(SessionSecurity):
    def __init__(
        self,
        settings: Settings | None = None,
    ):
        super().__init__(settings)

    def require_session(
        self, request: Request, db_session: Session = Depends(get_session)
    ) -> StaffSession:
        session = self.get_current_session(request, db_session)
        if session:
            if not isinstance(session, SessionType.STAFF.session_model):
                raise HTTPException(status_code=403, detail="Wrong session type")
            return session
        raise HTTPException(status_code=401, detail="Unauthorized")


@lru_cache
def get_general_security() -> GeneralSecurity:
    return GeneralSecurity()


@lru_cache
def get_staff_security() -> StaffSecurity:
    return StaffSecurity()


@lru_cache
def get_class_security() -> ClassSecurity:
    return ClassSecurity()
