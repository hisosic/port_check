"""Tests for rating feature."""

from __future__ import annotations

import os
import tempfile
import unittest

from recipe_service.models import Database, POINTS_RATING_GIVEN


class TestRatings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.author = self.db.create_user("chef", "chef@test.com", "pass1234")
        self.user1 = self.db.create_user("user1", "u1@test.com", "pass1234")
        self.user2 = self.db.create_user("user2", "u2@test.com", "pass1234")
        self.recipe = self.db.create_recipe(
            title="된장찌개", description="구수한 맛",
            instructions="1. 끓인다", author_id=self.author.id,
            ingredients=[{"name": "된장"}, {"name": "두부"}],
        )

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_rate_recipe(self):
        result = self.db.rate_recipe(self.recipe.id, self.user1.id, 4)
        self.assertEqual(result["score"], 4)
        self.assertTrue(result["is_new"])
        self.assertEqual(result["rating_avg"], 4.0)
        self.assertEqual(result["rating_count"], 1)

    def test_rate_updates_recipe(self):
        self.db.rate_recipe(self.recipe.id, self.user1.id, 5)
        self.db.rate_recipe(self.recipe.id, self.user2.id, 3)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.rating_avg, 4.0)
        self.assertEqual(recipe.rating_count, 2)

    def test_update_existing_rating(self):
        self.db.rate_recipe(self.recipe.id, self.user1.id, 2)
        result = self.db.rate_recipe(self.recipe.id, self.user1.id, 5)
        self.assertFalse(result["is_new"])
        self.assertEqual(result["rating_avg"], 5.0)
        self.assertEqual(result["rating_count"], 1)

    def test_first_rating_awards_points(self):
        pts_before = self.db.get_user(self.user1.id).points
        self.db.rate_recipe(self.recipe.id, self.user1.id, 4)
        pts_after = self.db.get_user(self.user1.id).points
        self.assertEqual(pts_after - pts_before, POINTS_RATING_GIVEN)

    def test_update_rating_no_extra_points(self):
        self.db.rate_recipe(self.recipe.id, self.user1.id, 3)
        pts_before = self.db.get_user(self.user1.id).points
        self.db.rate_recipe(self.recipe.id, self.user1.id, 5)
        pts_after = self.db.get_user(self.user1.id).points
        self.assertEqual(pts_after, pts_before)

    def test_cannot_rate_own_recipe(self):
        with self.assertRaises(ValueError, msg="본인 레시피"):
            self.db.rate_recipe(self.recipe.id, self.author.id, 5)

    def test_invalid_score_too_low(self):
        with self.assertRaises(ValueError, msg="1~5"):
            self.db.rate_recipe(self.recipe.id, self.user1.id, 0)

    def test_invalid_score_too_high(self):
        with self.assertRaises(ValueError, msg="1~5"):
            self.db.rate_recipe(self.recipe.id, self.user1.id, 6)

    def test_rate_nonexistent_recipe(self):
        with self.assertRaises(ValueError, msg="레시피를 찾을 수 없습니다"):
            self.db.rate_recipe(9999, self.user1.id, 3)

    def test_get_user_rating(self):
        self.assertIsNone(self.db.get_user_rating(self.recipe.id, self.user1.id))
        self.db.rate_recipe(self.recipe.id, self.user1.id, 4)
        self.assertEqual(self.db.get_user_rating(self.recipe.id, self.user1.id), 4)

    def test_get_recipe_ratings_distribution(self):
        self.db.rate_recipe(self.recipe.id, self.user1.id, 5)
        self.db.rate_recipe(self.recipe.id, self.user2.id, 3)
        info = self.db.get_recipe_ratings(self.recipe.id)
        self.assertEqual(info["average"], 4.0)
        self.assertEqual(info["count"], 2)
        self.assertEqual(info["distribution"][5], 1)
        self.assertEqual(info["distribution"][3], 1)
        self.assertEqual(info["distribution"][1], 0)

    def test_empty_ratings(self):
        info = self.db.get_recipe_ratings(self.recipe.id)
        self.assertEqual(info["average"], 0.0)
        self.assertEqual(info["count"], 0)


if __name__ == "__main__":
    unittest.main()
