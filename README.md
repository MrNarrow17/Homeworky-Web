# Homeworky

A lightweight homework-tracking web app for a school. Students join a class with a shared class password and browse assignments week by week; teachers ("staff") log in individually to post, edit, and remove homework, including photo attachments. Staff can be assigned to one or more classes, and admins can manage every class.

## Features

- **Two access levels** — a shared per-class password for students, individual accounts for staff (moderators and admins)
- **Staff can belong to multiple classes** — a class picker is shown on login for anyone managing more than one class; admins can access every class regardless of assignment
- **Week-by-week homework view**, navigated with HTMX partial updates (no full page reloads)
- **Photo attachments** on homework entries
- **Admin panel** (SQLAdmin) for creating and managing classes and staff accounts
- **Redis-backed sessions** with hashed opaque tokens, server-enforced expiry, and independent lifetimes for staff vs. class sessions
- **Automatic session revocation** — changing a staff member's password immediately invalidates all of their existing sessions
- **Rate limiting** on login and class-join endpoints, backed by Redis so it holds across multiple workers/replicas
- **Health check** that verifies both the database and Redis are reachable

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) + [SQLModel](https://sqlmodel.tiangolo.com/) for the backend and ORM
- [Alembic](https://alembic.sqlalchemy.org/) for database migrations
- [Redis](https://redis.io/) for sessions and rate limiting
- Jinja2 + [HTMX](https://htmx.org/) + Bootstrap for server-rendered UI
- [SQLAdmin](https://smithyhq.github.io/sqladmin/) for the admin panel
- PostgreSQL or SQLite, depending on `DATABASE_URL`
- [uv](https://docs.astral.sh/uv/) for dependency management

## Project structure

```
app/
  main.py           FastAPI app, routing, middleware, health check
  admin.py          SQLAdmin views for Class / Staff
  config.py         Settings, loaded from environment variables
  database.py       SQLModel engine, DB session, and Redis client
  logger.py         Structured JSON logging
  exceptions.py     Shared exception handling
  services.py       HomeworkService, SessionService (user-agent parsing, etc.)
  rate_limiting.py  Redis-backed rate limiter for login/join endpoints
  models/
    class_.py       Class table
    staff.py        Staff table (many-to-many with Class)
    homework.py     Homework table
    links.py        StaffClassLink — the staff↔class join table
  schemas/
    sessions.py     AppSession — the session payload stored in Redis
    class_.py, homework.py, staff.py   Request/response models
  security/
    redis.py        RedisSessionManager — issue/get/invalidate/revoke sessions
    dependencies.py ViewerDependencies — FastAPI auth dependencies
    hashing.py       PasswordSecurity — bcrypt password hashing, token hashing
  routers/
    classes.py      Student-facing routes (join class, view homework)
    staff.py        Staff-facing routes (login, class picker, manage homework)
  templates/        Jinja2 templates
  tools/            Small helpers (ISO week-range calculation)
alembic/            Database migrations
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A PostgreSQL database, or SQLite for local development
- A running Redis instance (sessions and rate limiting both depend on it — the app won't function without one)

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
REDIS_URL=redis://localhost:6379/0
TIMEDELTA=2
TOKEN_SECRET=change-me-to-a-long-random-string
SESSION_COOKIE=session
CLASS_SESSION_LIFETIME=315360000
STAFF_SESSION_LIFETIME=3600
RATE_LIMIT=5
BUCKET_KEY=rate-limit
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
```

| Variable                 | Required | Default                | Description                                                                                   |
| ------------------------ | -------- | ---------------------- | --------------------------------------------------------------------------------------------- |
| `APP_NAME`               | No       | `Homework APP`         | Display name for the app                                                                      |
| `DEBUG_MODE`             | No       | `false`                | Enables SQL query logging and allows non-HTTPS cookies. Keep `false` in production            |
| `DATABASE_URL`           | **Yes**  | —                      | SQLAlchemy connection string (PostgreSQL or SQLite)                                           |
| `REDIS_URL`              | **Yes**  | —                      | Redis connection string, used for sessions and rate limiting                                  |
| `TIMEDELTA`              | No       | `2`                    | UTC offset, in hours, used for "current time" and week calculations                           |
| `TOKEN_SECRET`           | **Yes**  | —                      | Long random secret used to hash session tokens. The app refuses to start without it           |
| `SESSION_COOKIE`         | No       | _(empty)_              | Name of the session cookie — set this explicitly                                              |
| `CLASS_SESSION_LIFETIME` | No       | `315360000` (10 years) | Student session lifetime, in seconds                                                          |
| `STAFF_SESSION_LIFETIME` | No       | `3600` (1 hour)        | Staff/admin session lifetime, in seconds — intentionally much shorter than the class lifetime |
| `RATE_LIMIT`             | No       | `5`                    | Minimum seconds between requests to a rate-limited endpoint (login, join), per client         |
| `BUCKET_KEY`             | No       | `rate-limit`           | Redis key prefix used by the rate limiter's bucket                                            |
| `ADMIN_USERNAME`         | No       | `admin`                | Login username for the `/admin` panel                                                         |
| `ADMIN_PASSWORD`         | No       | `admin`                | Login password for the `/admin` panel — change this before deploying                          |

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

The app runs at `http://localhost:8000`. A health check is available at `/health`, which returns `200` only if both the database and Redis are reachable, `503` otherwise.

## First-time use

There's no public sign-up flow — classes and staff accounts are created through the admin panel:

1. Go to `/admin` and log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
2. Create a **Class** (name + password) — this is the password students use to join.
3. Create a **Staff** member and assign them to one or more classes — this is the login teachers use to manage homework. Mark `is_admin` for someone who should be able to manage every class, or `is_mod` for someone scoped to their assigned classes.
4. Students visit `/classes/`, pick their class, and enter the class password.
5. Staff log in at `/staff/login/`. If they manage exactly one class, they're taken straight to its dashboard; if they manage more than one (or are an admin), they see a class picker first.

## Sessions

Sessions are stored in Redis, not the database — a session is an opaque, high-entropy token handed to the browser as an `httponly` cookie; the server only ever stores a hash of it. This means:

- **Expiry is enforced by Redis itself** (`SETEX`), not just trusted client-side — an expired session is actually gone, not just past its cookie's stated lifetime.
- **Staff and class sessions have independent lifetimes** — staff sessions default to 1 hour (privileged access), class sessions to 10 years (low-stakes, shared password, convenience-oriented).
- **Changing a staff member's password immediately revokes all of their active sessions**, wherever they're logged in.

## Rate limiting

Login (`/staff/login/`) and class-join (`/classes/join/`) are rate-limited per client IP, backed by a Redis bucket so the limit holds consistently even if the app is running multiple workers or replicas. Configure the limit via `RATE_LIMIT` (minimum seconds between requests) and `BUCKET_KEY` (the Redis key prefix, useful if you're sharing one Redis instance across multiple deployments).

## Database migrations

After changing a model under `app/models/`, generate and apply a migration:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

## Notes

- Session cookies are `httponly` and `samesite=lax`; `secure` is enabled automatically unless `DEBUG_MODE=true`.
- The `/uploads` path is served as public static files — anything saved there is reachable by direct URL.
- There's currently no automated test suite — verification is manual. Treat changes to `app/security/` and `app/rate_limiting.py` with extra care and test them by hand before deploying.

## License

No license has been specified for this project yet.
