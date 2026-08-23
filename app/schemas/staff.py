from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    username: str
    password: str


class LoginResponse(SQLModel):
    redirect_url: str
