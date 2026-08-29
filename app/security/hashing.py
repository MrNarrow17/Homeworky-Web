import hmac
from functools import lru_cache

import bcrypt

from app.config import Settings, get_settings


class PasswordSecurity:
    """
    A class for general security purposes.
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


@lru_cache
def get_password_security() -> PasswordSecurity:
    """
    A cached factory function for the PasswordSecurity object.
    """
    return PasswordSecurity()
