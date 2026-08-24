from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    """
    Schema for a login form request.
    """

    username: str
    password: str


class LoginResponse(SQLModel):
    """
    Schema for a login response.
    """

    redirect_url: str
