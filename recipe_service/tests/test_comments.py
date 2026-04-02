"""Tests for comment feature."""

from __future__ import annotations

import os
import tempfile
import unittest

from recipe_service.models import (
    Database,
    POINTS_COMMENT_WRITTEN,
    POINTS_FIRST_RECIPE_BONUS,
    POINTS_RECIPE_CREATED,
)


class TestComments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        # Create test user and recipe
        self.user = self.db.create_user("chef", "chef@test.com", "pass1234")
        self.other = self.db.create_user("fan", "fan@test.com", "pass1234")
        self.recipe = self.db.create_recipe(
            title="김치볶음밥", description="맛있는 볶음밥",
            instructions="1. 볶는다", author_id=self.user.id,
            ingredients=[{"name": "김치"}, {"name": "밥"}],
        )

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_add_comment(self):
        comment = self.db.add_comment(self.recipe.id, self.other.id, "맛있겠네요!")
        self.assertEqual(comment.content, "맛있겠네요!")
        self.assertEqual(comment.recipe_id, self.recipe.id)
        self.assertEqual(comment.user_id, self.other.id)
        self.assertGreater(comment.id, 0)

    def test_comment_awards_points(self):
        points_before = self.db.get_user(self.other.id).points
        self.db.add_comment(self.recipe.id, self.other.id, "좋아요!")
        points_after = self.db.get_user(self.other.id).points
        self.assertEqual(points_after - points_before, POINTS_COMMENT_WRITTEN)

    def test_comment_increments_count(self):
        self.db.add_comment(self.recipe.id, self.other.id, "댓글 1")
        self.db.add_comment(self.recipe.id, self.other.id, "댓글 2")
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.comment_count, 2)

    def test_get_comments(self):
        self.db.add_comment(self.recipe.id, self.other.id, "첫 번째")
        self.db.add_comment(self.recipe.id, self.user.id, "두 번째")
        comments = self.db.get_comments(self.recipe.id)
        self.assertEqual(len(comments), 2)
        # Newest first
        self.assertEqual(comments[0].content, "두 번째")
        self.assertEqual(comments[0].username, "chef")

    def test_get_comments_pagination(self):
        for i in range(5):
            self.db.add_comment(self.recipe.id, self.other.id, f"댓글 {i}")
        page = self.db.get_comments(self.recipe.id, offset=2, limit=2)
        self.assertEqual(len(page), 2)

    def test_update_comment(self):
        comment = self.db.add_comment(self.recipe.id, self.other.id, "원본")
        updated = self.db.update_comment(comment.id, self.other.id, "수정됨")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.content, "수정됨")
        self.assertGreaterEqual(updated.updated_at, updated.created_at)

    def test_update_comment_wrong_user(self):
        comment = self.db.add_comment(self.recipe.id, self.other.id, "원본")
        result = self.db.update_comment(comment.id, self.user.id, "해킹시도")
        self.assertIsNone(result)

    def test_delete_comment(self):
        comment = self.db.add_comment(self.recipe.id, self.other.id, "삭제할 댓글")
        self.assertTrue(self.db.delete_comment(comment.id, self.other.id))
        comments = self.db.get_comments(self.recipe.id)
        self.assertEqual(len(comments), 0)

    def test_delete_comment_decrements_count(self):
        c1 = self.db.add_comment(self.recipe.id, self.other.id, "댓글")
        self.assertEqual(self.db.get_recipe(self.recipe.id).comment_count, 1)
        self.db.delete_comment(c1.id, self.other.id)
        self.assertEqual(self.db.get_recipe(self.recipe.id).comment_count, 0)

    def test_delete_comment_wrong_user(self):
        comment = self.db.add_comment(self.recipe.id, self.other.id, "댓글")
        self.assertFalse(self.db.delete_comment(comment.id, self.user.id))

    def test_comment_on_nonexistent_recipe(self):
        with self.assertRaises(ValueError, msg="레시피를 찾을 수 없습니다"):
            self.db.add_comment(9999, self.other.id, "존재하지 않는 레시피")

    def test_empty_comment_rejected(self):
        with self.assertRaises(ValueError, msg="댓글 내용을 입력하세요"):
            self.db.add_comment(self.recipe.id, self.other.id, "   ")

    def test_too_long_comment_rejected(self):
        with self.assertRaises(ValueError, msg="2000자 이하"):
            self.db.add_comment(self.recipe.id, self.other.id, "x" * 2001)

    def test_comment_count_method(self):
        self.assertEqual(self.db.get_comment_count(self.recipe.id), 0)
        self.db.add_comment(self.recipe.id, self.other.id, "하나")
        self.assertEqual(self.db.get_comment_count(self.recipe.id), 1)

    def test_point_history_includes_comments(self):
        self.db.add_comment(self.recipe.id, self.other.id, "댓글")
        history = self.db.get_point_history(self.other.id)
        reasons = [h.reason for h in history]
        self.assertIn("댓글 작성", reasons)


if __name__ == "__main__":
    unittest.main()
