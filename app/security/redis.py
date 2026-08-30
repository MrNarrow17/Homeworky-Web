import secrets

from fastapi import Request, Response
from redis import Redis

from app.config import Settings, get_settings
from app.database import get_redis_client
from app.schemas.sessions import AppSession
from app.security.hashing import PasswordSecurity, get_password_security


class RedisSessionManager:
    def __init__(
        self,
        redis_client: Redis | None = None,
        settings: Settings | None = None,
        password_security: PasswordSecurity | None = None,
    ):
        self._redis_client = redis_client or get_redis_client()
        self._settings = settings or get_settings()
        self._password_security = password_security or get_password_security()
        self._session_cookie = self._settings.session_cookie

    def set_session_cookie(
        self, response: Response, token: str, lifetime: int
    ) -> Response:
        """
        Sets the session cookie in the response with the given token.
        """

        response.set_cookie(
            key=self._session_cookie,
            value=token,
            httponly=True,
            max_age=lifetime,
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
            key=self._session_cookie,
            httponly=True,
            samesite="lax",
            secure=not self._settings.debug_mode,
            path="/",
        )
        return response

    def issue_session(self, response: Response, session: AppSession) -> Response:
        """
        Issues a new session for the given user and sets the session cookie in the response.
        """

        if not session.is_authenticated:
            raise ValueError("Cannot issue session for non-authenticated user")

        opaque_token = secrets.token_urlsafe(64)
        token_hash = self._password_security.hash_token(opaque_token)

        self._redis_client.setex(
            name=f"session:{token_hash}",
            time=session.lifetime,
            value=session.model_dump_json(),
        )

        return self.set_session_cookie(response, opaque_token, session.lifetime)

    def get_session(self, request: Request) -> AppSession:
        """
        Retrieves the session for the given request.
        """

        opaque_token = request.cookies.get(self._session_cookie)
        if not opaque_token:
            return AppSession.from_raw_data(None)

        token_hash = self._password_security.hash_token(opaque_token)
        raw_data = self._redis_client.get(f"session:{token_hash}")
        return AppSession.from_raw_data(raw_data)

    def invalidate_session(self, request: Request, response: Response) -> Response:
        """
        Invalidates the session for the given request and response.
        """

        opaque_token = request.cookies.get(self._session_cookie)
        if not opaque_token:
            return response

        token_hash = self._password_security.hash_token(opaque_token)
        self._redis_client.delete(f"session:{token_hash}")

        return self.delete_session_cookie(response)


def get_session_manager(
    redis: Redis | None = None,
) -> RedisSessionManager:
    """
    Factory function for RedisSessionManager object.
    """
    return RedisSessionManager(redis)
