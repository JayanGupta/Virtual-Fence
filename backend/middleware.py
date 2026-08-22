"""
Virtual Fence — Middleware Stack
Request ID injection, security headers, and request timing.
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.logging_config import get_logger

logger = get_logger("middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID header into every request/response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Logs request method, path, status code, and response time."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip logging for high-frequency endpoints
        path = request.url.path
        skip_paths = ("/api/v1/video_feed", "/api/v1/snapshot", "/ws/")
        if any(path.startswith(s) for s in skip_paths):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            path,
            response.status_code,
            elapsed_ms,
        )
        return response
