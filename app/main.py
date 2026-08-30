import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from app.admin import AdminAuth, ClassAdmin, StaffAdmin
from app.config import get_settings
from app.database import engine
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def health():
    """
    Returns a 200 OK response for the health check.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
    )
