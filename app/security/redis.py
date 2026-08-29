import secrets

from fastapi import Request, Response
from redis import Redis
from user_agents import parse

from app.config import Settings, get_settings
from app.schemas.sessions import AppSession
from app.security.hashing import PasswordSecurity, get_password_security


class RedisSessionManager:
    def __init__(
        self,
        redis_client: Redis,
        settings: Settings | None = None,
        password_security: PasswordSecurity | None = None,
    ):
        self._redis_client = redis_client
        self._settings = settings or get_settings()
        self._password_security = password_security or get_password_security()
        self._session_cookie = self._settings.session_cookie
        self._session_lifetime = self._settings.session_lifetime

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

    def set_session_cookie(self, response: Response, token: str) -> Response:
        """
        Sets the session cookie in the response with the given token.
        """

        response.set_cookie(
            key=self._session_cookie,
            value=token,
            httponly=True,
            max_age=self._session_lifetime,
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

        opaque_token = secrets.token_urlsafe(64)
        token_hash = self._password_security.hash_token(opaque_token)
        redis_key = f"session:{token_hash}"

        self._redis_client.setex(
            name=redis_key, time=self._session_lifetime, value=session.model_dump_json()
        )

        return self.set_session_cookie(response, opaque_token)

    def get_session(self, request: Request) -> AppSession | None:
        """
        Retrieves the session for the given request.
        """
        opaque_token = request.cookies.get(self._session_cookie)
        if not opaque_token:
            return None

        token_hash = self._password_security.hash_token(opaque_token)
        raw_data = self._redis_client.get(f"session:{token_hash}")
        if not raw_data:
            return None

        return AppSession.model_validate_json(raw_data)

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


def get_session_manager(redis: Redis) -> RedisSessionManager:
    """FastAPI dependency provider for RedisSessionManager."""
    return RedisSessionManager(redis_client=redis)
