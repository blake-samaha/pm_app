"""Tests for authentication router error handling behavior."""

from __future__ import annotations

from typing import Tuple

from dependencies import get_auth_service
from exceptions import AuthenticationError
from main import app
from models import User


class _StubAuthService:
    """Minimal AuthService stub for router tests (avoids Firebase initialization)."""

    def __init__(
        self,
        *,
        login_error: Exception | None = None,
        superuser_error: Exception | None = None,
    ):
        self._login_error = login_error
        self._superuser_error = superuser_error

    def authenticate_with_firebase(self, token: str) -> Tuple[User, str]:
        raise self._login_error or AuthenticationError("Invalid Firebase token")

    def authenticate_superuser(self, email: str, password: str) -> Tuple[User, str]:
        raise self._superuser_error or AuthenticationError("Superuser not configured")


def test_superuser_login_errors_use_global_authentication_error_shape(client):
    """
    Before: `auth` router caught `Exception` and returned FastAPI's default
    `{"detail": ...}` shape via HTTPException.
    After: AuthenticationError bubbles to the global handler which returns the
    consistent error envelope.
    """
    app.dependency_overrides[get_auth_service] = lambda: _StubAuthService(
        superuser_error=AuthenticationError("Superuser not configured")
    )

    res = client.post(
        "/auth/superuser-login",
        json={"email": "admin@example.com", "password": "wrong"},
    )

    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"
    body = res.json()
    assert body["detail"] == "Superuser not configured"
    assert body["error_type"] == "AuthenticationError"
    assert body["status_code"] == 401


def test_login_unexpected_errors_return_500_not_401(client_no_raise):
    """
    Regression guard: non-auth failures should not be coerced into 401.
    """
    app.dependency_overrides[get_auth_service] = lambda: _StubAuthService(
        login_error=ValueError("boom")
    )

    res = client_no_raise.post("/auth/login", json={"token": "dummy"})

    assert res.status_code == 500
    body = res.json()
    assert body["status_code"] == 500
    assert body["error_type"] == "ValueError"
    assert body["detail"] == "boom"
