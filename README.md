# Homeworky

A lightweight homework-tracking web app for a school class. Students join with a shared class password and browse assignments week by week; teachers ("staff") log in individually to post, edit, and remove homework, including photo attachments.

## Features

- **Two access levels** — a shared per-class password for students, individual accounts for teachers/staff
- **Week-by-week homework view**, navigated with HTMX partial updates (no full page reloads)
- **Photo attachments** on homework entries
- **Admin panel** (SQLAdmin) for creating and managing classes and staff accounts
- **Cookie-based sessions** with hashed tokens and bcrypt-hashed passwords

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) + [SQLModel](https://sqlmodel.tiangolo.com/) for the backend and ORM
- [Alembic](https://alembic.sqlalchemy.org/) for database migrations
- Jinja2 + [HTMX](https://htmx.org/) + Bootstrap for server-rendered UI
- [SQLAdmin](https://smithyhq.github.io/sqladmin/) for the admin panel
- PostgreSQL or SQLite, depending on `DATABASE_URL`
- [uv](https://docs.astral.sh/uv/) for dependency management

## Project structure

```
app/
  main.py         FastAPI app, routing, middleware
  admin.py        SQLAdmin views for Class / StaffMember
  config.py       Settings, loaded from environment variables
  database.py     SQLModel engine and session
  security.py     Password hashing, session issuing/validation
  models/         SQLModel tables (class, homework, sessions, staff)
  schemas/        Request/response models
  routers/
    classes.py    Student-facing routes (join class, view homework)
    staff.py      Staff-facing routes (login, manage homework)
  templates/      Jinja2 templates
  tools/          Small helpers (ISO week-range calculation)
alembic/          Database migrations
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A PostgreSQL database, or SQLite for local development

## Setup

**1. Clone and install dependencies**

```bash
git clone <repository-url>
cd homeworky-web
uv sync
```

**2. Configure environment variables**

Create a `.env` file in the project root:

```env
APP_NAME=Homeworky
DEBUG_MODE=true
DATABASE_URL=sqlite:///./database.db
TIMEDELTA=2
TOKEN_SECRET=change-me-to-a-long-random-string
SESSION_COOKIE=session
CLASS_SESSION_LIFETIME=315360000
STAFF_SESSION_LIFETIME=315360000
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
```

| Variable                 | Required | Default                | Description                                                                                       |
| ------------------------ | -------- | ---------------------- | ------------------------------------------------------------------------------------------------- |
| `APP_NAME`               | No       | `Homework APP`         | Display name for the app                                                                          |
| `DEBUG_MODE`             | No       | `false`                | Enables SQL query logging and allows non-HTTPS cookies. Keep `false` in production                |
| `DATABASE_URL`           | **Yes**  | —                      | SQLAlchemy connection string (PostgreSQL or SQLite)                                               |
| `TIMEDELTA`              | No       | `2`                    | UTC offset, in hours, used for "current time" and week calculations                               |
| `TOKEN_SECRET`           | **Yes**  | —                      | Long random secret used to sign sessions and the admin panel. The app refuses to start without it |
| `SESSION_COOKIE`         | No       | _(empty)_              | Name of the session cookie — set this explicitly                                                  |
| `CLASS_SESSION_LIFETIME` | No       | `315360000` (10 years) | Student session lifetime, in seconds                                                              |
| `STAFF_SESSION_LIFETIME` | No       | `315360000` (10 years) | Staff session lifetime, in seconds                                                                |
| `ADMIN_USERNAME`         | No       | `admin`                | Login username for the `/admin` panel                                                             |
| `ADMIN_PASSWORD`         | No       | `admin`                | Login password for the `/admin` panel — change this before deploying                              |

Generate a strong `TOKEN_SECRET` with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**3. Set up the database**

```bash
uv run alembic upgrade head
```

**4. Create the uploads directory** (homework images are saved here, and the app won't start without it)

```bash
mkdir -p uploads
```

**5. Run the app**

```bash
uv run fastapi dev app/main.py
```

or, for a production-style run:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The app runs at `http://localhost:8000`. A health check is available at `/health`.

## First-time use

There's no public sign-up flow — classes and staff accounts are created through the admin panel:

1. Go to `/admin` and log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
2. Create a **Class** (name + password) — this is the password students use to join.
3. Create a **Staff** member and link them to that class — this is the login teachers use to manage homework.
4. Students visit `/classes/`, pick their class, and enter the class password.
5. Staff log in at `/staff/login/` to add, edit, or delete homework for their class.

## Database migrations

After changing a model under `app/models/`, generate and apply a migration:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

## Notes

- Session cookies are `httponly` and `samesite=lax`; `secure` is enabled automatically unless `DEBUG_MODE=true`.
- The `/uploads` path is served as public static files — anything saved there is reachable by direct URL.

## License

No license has been specified for this project yet.
