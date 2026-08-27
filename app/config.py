from datetime import datetime, timedelta, timezone
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global settings for the application.
    """

    app_name: str = Field(default="Homework APP", validation_alias="APP_NAME")
    debug_mode: bool = Field(default=False, validation_alias="DEBUG_MODE")
    database_url: SecretStr = Field(validation_alias="DATABASE_URL")
    time_delta: int = Field(default=3, validation_alias="TIMEDELTA")
    token_secret: str = Field(validation_alias="TOKEN_SECRET")

    hsts_value: str = Field(validation_alias="HSTS_VALUE")

    class_session_lifetime: int = Field(
        default=315360000, validation_alias="CLASS_SESSION_LIFETIME"
    )

    staff_session_lifetime: int = Field(
        default=3600, validation_alias="STAFF_SESSION_LIFETIME"
    )
    class_session_cookie: str = Field(validation_alias="CLASS_SESSION_COOKIE")
    staff_session_cookie: str = Field(validation_alias="STAFF_SESSION_COOKIE")
    admin_username: str = Field(validation_alias="ADMIN_USERNAME")
    admin_password: str = Field(validation_alias="ADMIN_PASSWORD")

    telegram_link: str = Field(validation_alias="TELEGRAM_LINK")

    logger_name: str = Field(default="app", validation_alias="LOGGER_NAME")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admin_username")
    def validate_admin_username(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("ADMIN_USERNAME must be set to a non-empty value")

        insecure_usernames = {"admin", "administrator", "root", "user", "test"}
        if v.lower() in insecure_usernames:
            raise ValueError(
                f"ADMIN_USERNAME cannot be set to common default value '{v}'. "
                "Please use a unique, non-default username for security."
            )

        return v

    @field_validator("admin_password")
    def validate_admin_password(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("ADMIN_PASSWORD must be set to a non-empty value")

        if len(v) < 5:
            raise ValueError(
                "ADMIN_PASSWORD must be at least 5 characters long for security"
            )

        insecure_passwords = {
            "admin",
            "password",
            "123456",
            "12345678",
            "password123",
            "admin123",
            "changeme",
            "change-me",
            "default",
        }
        if v.lower() in insecure_passwords:
            raise ValueError(
                "ADMIN_PASSWORD cannot be set to a common default value. "
                "Please use a strong, unique password for security."
            )

        return v

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
