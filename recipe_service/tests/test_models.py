"""Tests for database models and operations."""

from __future__ import annotations

import os
import tempfile
import unittest

from recipe_service.models import (
    Database,
    POINTS_FIRST_RECIPE_BONUS,
    POINTS_RECIPE_CREATED,
    POINTS_RECIPE_LIKED,
    hash_password,
    verify_password,
)


class TestPasswordHashing(unittest.TestCase):
    def test_hash_and_verify(self):
        pw = "my_secret_123"
        hashed = hash_password(pw)
        self.assertTrue(verify_password(pw, hashed))

    def test_wrong_password(self):
        hashed = hash_password("correct")
        self.assertFalse(verify_password("wrong", hashed))

    def test_hash_is_salted(self):
        pw = "same_password"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        self.assertNotEqual(h1, h2)  # Different salts


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    # --- User tests ---

    def test_create_and_get_user(self):
        user = self.db.create_user("chef1", "chef1@test.com", "pass123")
        self.assertEqual(user.username, "chef1")
        self.assertEqual(user.points, 0)

        fetched = self.db.get_user(user.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.username, "chef1")

    def test_duplicate_username(self):
        self.db.create_user("chef1", "a@test.com", "pass")
        with self.assertRaises(ValueError):
            self.db.create_user("chef1", "b@test.com", "pass")

    def test_duplicate_email(self):
        self.db.create_user("chef1", "same@test.com", "pass")
        with self.assertRaises(ValueError):
            self.db.create_user("chef2", "same@test.com", "pass")

    def test_authenticate_success(self):
        self.db.create_user("chef1", "c@test.com", "mypass")
        user = self.db.authenticate("chef1", "mypass")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "chef1")

    def test_authenticate_fail(self):
        self.db.create_user("chef1", "c@test.com", "mypass")
        user = self.db.authenticate("chef1", "wrongpass")
        self.assertIsNone(user)

    # --- Recipe tests ---

    def test_create_recipe_awards_first_bonus(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        recipe = self.db.create_recipe(
            title="김치찌개",
            description="매콤한 김치찌개",
            instructions="1. 김치를 볶는다\n2. 물을 넣는다\n3. 끓인다",
            author_id=user.id,
            ingredients=[
                {"name": "김치", "amount": "200", "unit": "g"},
                {"name": "돼지고기", "amount": "100", "unit": "g"},
                {"name": "두부", "amount": "1", "unit": "모"},
            ],
            cooking_time_min=30,
            difficulty="easy",
        )
        self.assertIsNotNone(recipe.id)
        self.assertEqual(recipe.title, "김치찌개")

        # First recipe bonus
        updated = self.db.get_user(user.id)
        self.assertEqual(updated.points, POINTS_RECIPE_CREATED + POINTS_FIRST_RECIPE_BONUS)

    def test_second_recipe_no_bonus(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        self.db.create_recipe(
            title="Recipe 1", description="", instructions="step 1",
            author_id=user.id, ingredients=[{"name": "salt"}],
        )
        first_points = self.db.get_user(user.id).points

        self.db.create_recipe(
            title="Recipe 2", description="", instructions="step 1",
            author_id=user.id, ingredients=[{"name": "pepper"}],
        )
        second_points = self.db.get_user(user.id).points

        # Second recipe: only POINTS_RECIPE_CREATED, no bonus
        self.assertEqual(second_points - first_points, POINTS_RECIPE_CREATED)

    def test_get_recipe_with_author(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        recipe = self.db.create_recipe(
            title="Test", description="", instructions="do it",
            author_id=user.id, ingredients=[{"name": "egg"}],
        )
        fetched = self.db.get_recipe(recipe.id)
        self.assertEqual(fetched.author_name, "chef")

    def test_get_recipe_ingredients(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        recipe = self.db.create_recipe(
            title="Omelette", description="", instructions="cook",
            author_id=user.id,
            ingredients=[
                {"name": "계란", "amount": "3", "unit": "개"},
                {"name": "우유", "amount": "50", "unit": "ml"},
            ],
        )
        ingredients = self.db.get_recipe_ingredients(recipe.id)
        self.assertEqual(len(ingredients), 2)
        names = {i.name for i in ingredients}
        self.assertIn("계란", names)
        self.assertIn("우유", names)

    def test_list_recipes(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        for i in range(5):
            self.db.create_recipe(
                title=f"Recipe {i}", description="", instructions="step",
                author_id=user.id, ingredients=[{"name": f"item{i}"}],
            )
        recipes = self.db.list_recipes(limit=3)
        self.assertEqual(len(recipes), 3)

    def test_delete_recipe(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        recipe = self.db.create_recipe(
            title="ToDelete", description="", instructions="step",
            author_id=user.id, ingredients=[{"name": "x"}],
        )
        self.assertTrue(self.db.delete_recipe(recipe.id, user.id))
        self.assertIsNone(self.db.get_recipe(recipe.id))

    def test_delete_recipe_wrong_user(self):
        user1 = self.db.create_user("chef1", "a@test.com", "pass")
        user2 = self.db.create_user("chef2", "b@test.com", "pass")
        recipe = self.db.create_recipe(
            title="Mine", description="", instructions="step",
            author_id=user1.id, ingredients=[{"name": "x"}],
        )
        self.assertFalse(self.db.delete_recipe(recipe.id, user2.id))

    # --- Ingredient matching tests ---

    def test_find_recipes_by_ingredients_full_match(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        self.db.create_recipe(
            title="계란볶음밥",
            description="", instructions="볶는다",
            author_id=user.id,
            ingredients=[
                {"name": "계란", "amount": "2", "unit": "개"},
                {"name": "밥", "amount": "1", "unit": "공기"},
                {"name": "파", "amount": "1", "unit": "줄기"},
            ],
        )
        results = self.db.find_recipes_by_ingredients(["계란", "밥", "파"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["match_ratio"], 1.0)
        self.assertEqual(results[0]["missing_count"], 0)

    def test_find_recipes_partial_match(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        self.db.create_recipe(
            title="된장찌개",
            description="", instructions="끓인다",
            author_id=user.id,
            ingredients=[
                {"name": "된장"},
                {"name": "두부"},
                {"name": "감자"},
                {"name": "호박"},
            ],
        )
        # 2/4 match = 0.5
        results = self.db.find_recipes_by_ingredients(
            ["된장", "두부"], min_match_ratio=0.5,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["match_ratio"], 0.5)
        self.assertEqual(results[0]["missing_count"], 2)

    def test_find_recipes_below_threshold(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        self.db.create_recipe(
            title="Complex",
            description="", instructions="step",
            author_id=user.id,
            ingredients=[{"name": f"ing{i}"} for i in range(10)],
        )
        # Only 1/10 match = 0.1, below 0.3 threshold
        results = self.db.find_recipes_by_ingredients(["ing0"], min_match_ratio=0.3)
        self.assertEqual(len(results), 0)

    def test_find_recipes_empty_ingredients(self):
        results = self.db.find_recipes_by_ingredients([])
        self.assertEqual(results, [])

    # --- Like tests ---

    def test_toggle_like(self):
        user1 = self.db.create_user("chef", "a@test.com", "pass")
        user2 = self.db.create_user("fan", "b@test.com", "pass")
        recipe = self.db.create_recipe(
            title="Tasty", description="", instructions="step",
            author_id=user1.id, ingredients=[{"name": "x"}],
        )

        # Like
        result = self.db.toggle_like(user2.id, recipe.id)
        self.assertTrue(result["liked"])
        self.assertEqual(result["like_count"], 1)
        self.assertTrue(self.db.is_liked(user2.id, recipe.id))

        # Author gets points
        author = self.db.get_user(user1.id)
        expected = POINTS_RECIPE_CREATED + POINTS_FIRST_RECIPE_BONUS + POINTS_RECIPE_LIKED
        self.assertEqual(author.points, expected)

        # Unlike
        result = self.db.toggle_like(user2.id, recipe.id)
        self.assertFalse(result["liked"])
        self.assertEqual(result["like_count"], 0)
        self.assertFalse(self.db.is_liked(user2.id, recipe.id))

    def test_self_like_no_points(self):
        user = self.db.create_user("chef", "a@test.com", "pass")
        recipe = self.db.create_recipe(
            title="Mine", description="", instructions="step",
            author_id=user.id, ingredients=[{"name": "x"}],
        )
        points_before = self.db.get_user(user.id).points
        self.db.toggle_like(user.id, recipe.id)
        points_after = self.db.get_user(user.id).points
        # Self-like should not award additional points
        self.assertEqual(points_before, points_after)

    # --- Points tests ---

    def test_point_history(self):
        user = self.db.create_user("chef", "c@test.com", "pass")
        self.db.create_recipe(
            title="R1", description="", instructions="s",
            author_id=user.id, ingredients=[{"name": "x"}],
        )
        history = self.db.get_point_history(user.id)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0].reason, "첫 레시피 등록 보너스")

    def test_leaderboard(self):
        for i in range(3):
            user = self.db.create_user(f"chef{i}", f"c{i}@test.com", "pass")
            for j in range(i + 1):
                self.db.create_recipe(
                    title=f"R{i}_{j}", description="", instructions="s",
                    author_id=user.id, ingredients=[{"name": "x"}],
                )

        leaders = self.db.get_leaderboard(limit=3)
        self.assertEqual(len(leaders), 3)
        # Highest points first
        self.assertGreaterEqual(leaders[0].points, leaders[1].points)
        self.assertGreaterEqual(leaders[1].points, leaders[2].points)


if __name__ == "__main__":
    unittest.main()
