from fastapi import status
from fastapi.exceptions import HTTPException


class ClassNotFoundException(HTTPException):
    """
    An exception raised when a class is not found.
    """

    def __init__(self, class_id: int | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with id {class_id} not found"
            if class_id is not None
            else "Class not found",
        )


class HomeworkNotFoundException(HTTPException):
    """
    An exception raised when a homework is not found.
    """

    def __init__(self, homework_id: int | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Homework with id {homework_id} not found"
            if homework_id is not None
            else "Homework not found",
        )


class WrongPasswordException(HTTPException):
    """
    An exception raised when the password is wrong.
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong password",
        )


class InvalidCredentialsException(HTTPException):
    """
    An exception raised when the credentials are invalid.
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
