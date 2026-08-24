from datetime import datetime, timedelta, timezone
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global settings for the application.
    """

    app_name: str = Field(default="Homework APP", validation_alias="APP_NAME")
    debug_mode: bool = Field(default=False, validation_alias="DEBUG_MODE")
    database_url: SecretStr = Field(
        default=SecretStr(""), validation_alias="DATABASE_URL"
    )
    time_delta: int = Field(default=2, validation_alias="TIMEDELTA")
    token_secret: str = Field(default="", validation_alias="TOKEN_SECRET")

    class_session_lifetime: int = Field(
        default=315360000, validation_alias="CLASS_SESSION_LIFETIME"
    )

    staff_session_lifetime: int = Field(
        default=315360000, validation_alias="STAFF_SESSION_LIFETIME"
    )
    class_session_cookie: str = Field(
        default="", validation_alias="CLASS_SESSION_COOKIE"
    )
    staff_session_cookie: str = Field(
        default="", validation_alias="STAFF_SESSION_COOKIE"
    )
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", validation_alias="ADMIN_PASSWORD")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def timezone(self) -> timezone:
        return timezone(timedelta(hours=self.time_delta))

    @property
    def current_time(self) -> datetime:
        return datetime.now(self.timezone)


@lru_cache
def get_settings() -> Settings:
    """
    A cached factory function for the Settings object.
    """
    return Settings()
