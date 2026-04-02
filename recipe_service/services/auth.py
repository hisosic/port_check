"""Authentication service using simple token-based auth."""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

from recipe_service.models import Database, User

# In-memory token store (for production, use Redis or JWT)
_tokens: dict[str, dict[str, Any]] = {}
TOKEN_EXPIRY_SECONDS = 86400  # 24 hours


def generate_token(user_id: int) -> str:
    """Generate an auth token for a user."""
    token = secrets.token_urlsafe(32)
    _tokens[token] = {
        "user_id": user_id,
        "created_at": time.time(),
    }
    return token


def validate_token(token: str) -> int | None:
    """Validate a token and return user_id, or None if invalid."""
    info = _tokens.get(token)
    if not info:
        return None
    if time.time() - info["created_at"] > TOKEN_EXPIRY_SECONDS:
        _tokens.pop(token, None)
        return None
    return info["user_id"]


def revoke_token(token: str) -> None:
    """Revoke a token (logout)."""
    _tokens.pop(token, None)


def register_user(
    db: Database, username: str, email: str, password: str,
) -> dict[str, Any]:
    """Register a new user and return user info with token."""
    if len(username) < 2:
        raise ValueError("사용자명은 2자 이상이어야 합니다")
    if len(password) < 4:
        raise ValueError("비밀번호는 4자 이상이어야 합니다")
    if "@" not in email:
        raise ValueError("유효한 이메일 주소를 입력하세요")

    user = db.create_user(username, email, password)
    token = generate_token(user.id)
    return {
        "user": _user_dict(user),
        "token": token,
    }


def login_user(
    db: Database, username: str, password: str,
) -> dict[str, Any]:
    """Authenticate and return user info with token."""
    user = db.authenticate(username, password)
    if not user:
        raise ValueError("사용자명 또는 비밀번호가 올바르지 않습니다")
    token = generate_token(user.id)
    return {
        "user": _user_dict(user),
        "token": token,
    }


def get_current_user(db: Database, token: str) -> User:
    """Get the authenticated user from a token."""
    user_id = validate_token(token)
    if not user_id:
        raise PermissionError("인증이 필요합니다. 로그인해주세요.")
    user = db.get_user(user_id)
    if not user:
        raise PermissionError("사용자를 찾을 수 없습니다")
    return user


def _user_dict(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "points": user.points,
        "created_at": user.created_at,
    }
