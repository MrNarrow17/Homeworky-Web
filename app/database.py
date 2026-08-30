from functools import lru_cache

from redis import Redis
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=settings.debug_mode,
)


def init_db() -> None:
    """
    Initializes the database by creating all tables defined in the SQLModel metadata.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    A cached factory function for the Settings object.
    """
    with Session(engine) as session:
        yield session


@lru_cache
def get_redis_client() -> Redis:
    """
    A cached factory function for the Redis client.
    """
    settings = get_settings()
    return Redis.from_url(
        settings.redis_url.get_secret_value(),
        decode_responses=True,
    )
