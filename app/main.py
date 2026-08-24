from dotenv import load_dotenv
from fastapi.responses import RedirectResponse

load_dotenv()

import os
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from fastapi import FastAPI, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from alembic import command
from app.admin import AdminAuth, ClassAdmin, StaffAdmin
from app.config import get_settings
from app.database import engine, init_db
from app.routers import classes, staff

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent.parent


def run_migrations():
    ini_path = os.path.join(BASE_DIR, "alembic.ini")
    alembic_cfg = Config(ini_path)
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(run_migrations)
    init_db()
    yield


app = FastAPI(title="My FastAPI App", version="1.0.0", lifespan=lifespan)

authentication_backend = AdminAuth(secret_key=settings.token_secret)
admin = Admin(app, engine, authentication_backend=authentication_backend)

app.add_middleware(SessionMiddleware, secret_key=settings.token_secret)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(classes.router, prefix="/classes")
app.include_router(staff.router)

admin.add_view(ClassAdmin)
admin.add_view(StaffAdmin)


@app.get("/")
async def root():
    return RedirectResponse(url="/classes/")


@app.head("/")
async def root_head():
    return Response(status_code=200)
