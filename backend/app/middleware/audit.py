# -*- coding: utf-8 -*-
"""
Audit Middleware
审计中间件
"""
import time
import json
import uuid
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("audit")


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""

    AUDIT_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/logout",
        "/api/v1/users",
        "/api/v1/defect",
        "/api/v1/timeseries",
        "/api/v1/industrial",
    ]

    IGNORE_PATHS = ["/health", "/docs", "/openapi.json", "/redoc", "/static"]

    SENSITIVE_FIELDS = ["password", "token", "secret", "access_token", "refresh_token"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if self._should_ignore(path):
            return await call_next(request)

        start_time = time.time()

        # Add request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        process_time = time.time() - start_time

        if self._should_audit(path, request.method):
            log_entry = {
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "ip": self._get_client_ip(request),
            }
            logger.info(json.dumps(log_entry, ensure_ascii=False))

        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        response.headers["X-Request-ID"] = request_id

        return response

    def _should_ignore(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.IGNORE_PATHS)

    def _should_audit(self, path: str, method: str) -> bool:
        if method == "GET":
            return False
        return any(path.startswith(p) for p in self.AUDIT_PATHS)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        self._cleanup_old_records(current_time)

        if client_ip in self.request_counts:
            count = self.request_counts[client_ip]["count"]
            if count >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {"code": "RATE_LIMIT_EXCEEDED", "message": "请求过于频繁，请稍后再试"},
                    },
                )
            self.request_counts[client_ip]["count"] += 1
        else:
            self.request_counts[client_ip] = {"count": 1, "start_time": current_time}

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _cleanup_old_records(self, current_time: float):
        expired = [ip for ip, d in self.request_counts.items()
                   if current_time - d["start_time"] > self.window_seconds]
        for ip in expired:
            del self.request_counts[ip]
