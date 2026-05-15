"""
Custom middleware for request logging and rate limiting.
"""

import time
import logging
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("knowledge_os.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and latency."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        # Inject timing header for observability
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory token-bucket rate limiter keyed by client IP.

    For production, replace with Redis-backed rate limiting.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Prune old entries
        self._buckets[client_ip] = [
            t for t in self._buckets[client_ip] if t > window_start
        ]

        if len(self._buckets[client_ip]) >= self.max_requests:
            return True

        self._buckets[client_ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if self._is_rate_limited(client_ip):
            logger.warning("Rate limit exceeded for %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        return await call_next(request)
