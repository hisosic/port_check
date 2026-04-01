"""Tests for authentication service."""

from __future__ import annotations

import os
import tempfile
import unittest

from recipe_service.models import Database
from recipe_service.services.auth import (
    generate_token,
    get_current_user,
    login_user,
    register_user,
    revoke_token,
    validate_token,
)


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_register_and_login(self):
        result = register_user(self.db, "testuser", "test@test.com", "password123")
        self.assertIn("token", result)
        self.assertEqual(result["user"]["username"], "testuser")

        login_result = login_user(self.db, "testuser", "password123")
        self.assertIn("token", login_result)

    def test_register_short_username(self):
        with self.assertRaises(ValueError, msg="사용자명은 2자 이상"):
            register_user(self.db, "a", "a@test.com", "password")

    def test_register_short_password(self):
        with self.assertRaises(ValueError, msg="비밀번호는 4자 이상"):
            register_user(self.db, "user", "a@test.com", "12")

    def test_register_invalid_email(self):
        with self.assertRaises(ValueError, msg="유효한 이메일"):
            register_user(self.db, "user", "not-an-email", "password")

    def test_login_wrong_password(self):
        register_user(self.db, "user", "a@test.com", "correct")
        with self.assertRaises(ValueError):
            login_user(self.db, "user", "wrong")

    def test_token_validation(self):
        result = register_user(self.db, "user", "a@test.com", "pass1234")
        token = result["token"]
        user_id = validate_token(token)
        self.assertEqual(user_id, result["user"]["id"])

    def test_token_revoke(self):
        result = register_user(self.db, "user", "a@test.com", "pass1234")
        token = result["token"]
        revoke_token(token)
        self.assertIsNone(validate_token(token))

    def test_get_current_user(self):
        result = register_user(self.db, "user", "a@test.com", "pass1234")
        user = get_current_user(self.db, result["token"])
        self.assertEqual(user.username, "user")

    def test_get_current_user_invalid_token(self):
        with self.assertRaises(PermissionError):
            get_current_user(self.db, "invalid_token")


if __name__ == "__main__":
    unittest.main()
