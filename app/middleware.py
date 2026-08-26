import secrets
import time
from logging import Logger

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings

settings = get_settings()


class HSTSMiddleware:
    """
    Middleware for setting HTTP Strict Transport Security (HSTS) headers.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_hsts(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (
                        b"strict-transport-security",
                        settings.hsts_value.encode("ascii"),
                    )
                )

                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_hsts)


class CSPMiddleware:
    """
    Middleware for setting secure Content Security Policy (CSP) headers with Nonce.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or settings.debug_mode:
            await self.app(scope, receive, send)
            return

        nonce = secrets.token_urlsafe(16)
        scope["csp_nonce"] = nonce

        csp_policy = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval' https://jsdelivr.net https://cloudflare.com; "
            f"style-src 'self' 'nonce-{nonce}' https://jsdelivr.net https://googleapis.com https://cloudflare.com; "
            f"style-src-attr 'unsafe-inline'; "
            f"font-src 'self' https://gstatic.com https://cloudflare.com; "
            f"img-src 'self' data: https://tiangolo.com; "
            f"frame-ancestors 'none';"
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append(
                    (b"content-security-policy", csp_policy.encode("latin-1"))
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)


class LoggingMiddleware:
    """
    Middleware for logging HTTP requests and responses.
    """

    def __init__(self, app: ASGIApp, logger: Logger):
        self.app = app
        self.logger = logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]
        client = scope.get("client")
        client_host = client[0] if client else "unknown"

        status_code = None
        start_time = time.perf_counter()

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)

        process_time = time.perf_counter() - start_time
        log_extra = {
            "http_method": method,
            "path": path,
            "status_code": status_code,
            "duration_seconds": round(process_time, 4),
            "client_host": client_host,
        }
        self.logger.info(f"Request processed: {method} {path}", extra=log_extra)
