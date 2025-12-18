"""Request logging middleware for timing and completion logging."""

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request completion with timing information.

    Logs:
    - HTTP status code
    - Request duration in milliseconds
    - Uses structlog context (request_id, path, method) from RequestContextMiddleware
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request completion (context vars from RequestContextMiddleware included)
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
