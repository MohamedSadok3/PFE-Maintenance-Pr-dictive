"""
Unit tests for AuthService and shared JWT utilities.

Database and bcrypt calls are mocked — no real PostgreSQL required.

Run with:
    pytest backend/tests/test_auth_service.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Resolve import paths
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ.setdefault("POSTGRES_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("JWT_SECRET",   "test-secret-for-unit-tests")


# ── JWT utilities ────────────────────────────────────────────────────────────

class TestJWT:
    def test_create_and_decode_token(self):
        from shared.auth import create_token, decode_token

        user = MagicMock()
        user.id       = 42
        user.email    = "test@example.com"
        user.name     = "Test User"
        user.role     = "admin"
        user.machines = ["moteur"]
        user.plant_id = 1

        token   = create_token(user, expires_hours=1)
        payload = decode_token(token)

        assert payload["sub"]      == "42"
        assert payload["email"]    == "test@example.com"
        assert payload["role"]     == "admin"
        assert payload["plant_id"] == 1

    def test_expired_token_raises(self):
        import jwt
        from shared.auth import JWT_SECRET
        from shared.constants import JWT_ALGORITHM
        from datetime import datetime, timedelta, timezone

        expired_payload = {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        with pytest.raises(jwt.ExpiredSignatureError):
            from shared.auth import decode_token
            decode_token(token)

    def test_tampered_token_raises(self):
        import jwt
        from shared.auth import create_token, decode_token

        user = MagicMock()
        user.id = 1; user.email = "a@b.com"; user.name = "A"
        user.role = "admin"; user.machines = []; user.plant_id = 1

        token   = create_token(user)
        tampered = token[:-4] + "XXXX"

        with pytest.raises(jwt.InvalidTokenError):
            decode_token(tampered)


# ── AuthService.authenticate_user ───────────────────────────────────────────

class TestAuthenticateUser:
    def _make_service(self):
        with patch("services.auth_service.get_db_connection"):
            from services.auth_service import AuthService
            return AuthService()

    def test_wrong_password_returns_none(self):
        import bcrypt

        real_hash = bcrypt.hashpw(b"correct_password", bcrypt.gensalt()).decode()

        mock_row = {
            "id": 1, "name": "Alice", "email": "alice@test.com",
            "password_hash": real_hash, "role": "admin",
            "plant_id": 1, "machines": [], "last_login": None, "created_at": None,
        }

        svc = self._make_service()

        with patch("services.auth_service.get_db_connection") as mock_conn:
            mock_ctx  = MagicMock()
            mock_cur  = MagicMock()
            mock_cur.fetchone.return_value = mock_row
            mock_ctx.cursor.return_value.__enter__.return_value = mock_cur
            mock_ctx.cursor.return_value.__exit__  = MagicMock(return_value=False)
            mock_conn.return_value.__enter__.return_value = mock_ctx
            mock_conn.return_value.__exit__  = MagicMock(return_value=False)

            result = svc.authenticate_user("alice@test.com", "wrong_password")
            assert result is None

    def test_correct_password_returns_user(self):
        import bcrypt
        from models.models import User

        real_hash = bcrypt.hashpw(b"correct_password", bcrypt.gensalt()).decode()

        mock_row = {
            "id": 1, "name": "Alice", "email": "alice@test.com",
            "password_hash": real_hash, "role": "admin",
            "plant_id": 1, "machines": [], "last_login": None, "created_at": None,
        }

        svc = self._make_service()

        with patch("services.auth_service.get_db_connection") as mock_conn:
            mock_ctx = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = mock_row
            mock_ctx.cursor.return_value.__enter__.return_value = mock_cur
            mock_ctx.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.__enter__.return_value = mock_ctx
            mock_conn.return_value.__exit__  = MagicMock(return_value=False)

            result = svc.authenticate_user("alice@test.com", "correct_password")
            assert isinstance(result, User)
            assert result.email == "alice@test.com"

    def test_nonexistent_user_returns_none(self):
        svc = self._make_service()

        with patch("services.auth_service.get_db_connection") as mock_conn:
            mock_ctx = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = None
            mock_ctx.cursor.return_value.__enter__.return_value = mock_cur
            mock_ctx.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.__enter__.return_value = mock_ctx
            mock_conn.return_value.__exit__  = MagicMock(return_value=False)

            result = svc.authenticate_user("nobody@test.com", "anything")
            assert result is None


# ── AuthService.update_profile ───────────────────────────────────────────────

class TestUpdateProfile:
    def _make_service(self):
        with patch("services.auth_service.get_db_connection"):
            from services.auth_service import AuthService
            return AuthService()

    def test_no_fields_returns_error(self):
        svc = self._make_service()
        user, error = svc.update_profile(1, {})
        assert user is None
        assert error is not None

    def test_new_password_too_short_returns_error(self):
        svc = self._make_service()
        user, error = svc.update_profile(1, {
            "current_password": "old",
            "new_password": "abc",   # < 6 chars
        })
        assert user is None
        assert "6" in error

    def test_new_password_requires_current_password(self):
        svc = self._make_service()
        user, error = svc.update_profile(1, {
            "new_password": "newpassword123",
            # missing current_password
        })
        assert user is None
        assert error is not None
