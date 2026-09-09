from pydantic import ConfigDict
from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    """
    Schema for a login form request.
    """

    model_config = ConfigDict(str_strip_whitespace=True)  # type: ignore

    username: str
    password: str


class LoginResponse(SQLModel):
    """
    Schema for a login response.
    """

    redirect_url: str
