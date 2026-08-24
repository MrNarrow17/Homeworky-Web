from dotenv import load_dotenv
from fastapi.responses import RedirectResponse

load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from app.admin import AdminAuth, ClassAdmin, StaffAdmin
from app.config import get_settings
from app.database import engine, init_db, run_migrations
from app.routers import classes, staff

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
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
