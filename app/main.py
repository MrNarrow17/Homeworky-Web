import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqladmin import Admin
from sqlmodel import Session, select
from starlette.middleware.sessions import SessionMiddleware

from app.admin import AdminAuth, ClassAdmin, StaffAdmin
from app.config import get_settings
from app.database import engine, get_redis_client, get_session
from app.logger import get_app_logger
from app.middleware import HSTSMiddleware, LoggingMiddleware
from app.routers import classes, staff

settings = get_settings()
app_logger_instance = get_app_logger()
logger = app_logger_instance.logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False

    yield


app = FastAPI(title="My FastAPI App", version="1.0.0", lifespan=lifespan)
authentication_backend = AdminAuth(secret_key=settings.token_secret.get_secret_value())
admin = Admin(app, engine, authentication_backend=authentication_backend)


app.add_middleware(LoggingMiddleware, logger=logger)
app.add_middleware(
    SessionMiddleware, secret_key=settings.token_secret.get_secret_value()
)
app.add_middleware(HSTSMiddleware)


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(classes.router, prefix="/classes")
app.include_router(staff.router)

admin.add_view(ClassAdmin)
admin.add_view(StaffAdmin)

exception_templates = Jinja2Templates(directory="app/templates/exceptions")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return exception_templates.TemplateResponse(
        request,
        name="error.html",
        context={
            "request": request,
            "status_code": exc.status_code,
            "telegram": settings.telegram_link,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def redis_down_handler(request: Request, exc: RuntimeError):
    return exception_templates.TemplateResponse(
        request,
        name="error.html",
        context={
            "request": request,
            "status_code": 500,
            "telegram": settings.telegram_link,
        },
    )


@app.get("/")
def root():
    """
    Redirects to the classes page.
    """
    return RedirectResponse(url="/classes/")


@app.head("/")
def root_head():
    """
    Returns a 200 OK response for the health check.
    """
    return Response(status_code=200)


@app.get("/health")
async def health(db_session: Session = Depends(get_session)):
    """
    Returns a 200 OK response if the Redis and database are available, otherwise returns a 503 Service Unavailable response.
    """
    redis_ok = True
    try:
        await get_redis_client().ping()
    except Exception:
        redis_ok = False
    db_ok = True
    try:
        db_session.exec(select(1))
    except Exception:
        db_ok = False
    status_code = 200 if redis_ok and db_ok else 503
    return JSONResponse({"redis": redis_ok, "db": db_ok}, status_code=status_code)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
    )
