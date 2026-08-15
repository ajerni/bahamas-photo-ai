from __future__ import annotations

import base64
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.config import get_settings


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.basic_auth_enabled:
            return await call_next(request)
        if _credentials_match(
            request.headers.get("authorization"),
            settings.reverse_proxy_user,
            settings.reverse_proxy_password,
        ):
            return await call_next(request)
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Private Memory Map"'},
            content="Authentication required",
        )


def _credentials_match(header: str | None, user: str, password: str) -> bool:
    if not header or not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:].strip()).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    if ":" not in decoded:
        return False
    given_user, given_password = decoded.split(":", 1)
    return _digest_equal(given_user, user) and _digest_equal(given_password, password)


def _digest_equal(left: str, right: str) -> bool:
    left_bytes = left.encode("utf-8")
    right_bytes = right.encode("utf-8")
    if len(left_bytes) != len(right_bytes):
        return False
    return secrets.compare_digest(left_bytes, right_bytes)
