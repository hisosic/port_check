"""Tests for 10 new features: replies, profiles, images, nutrition,
steps, ingredient prices, badges, recommendations, advanced filter, timers."""

import os
import tempfile
import time
import unittest

from recipe_service.models import Database


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.alice = self.db.create_user("alice", "alice@test.com", "pass1234")
        self.bob = self.db.create_user("bob", "bob@test.com", "pass1234")
        self.recipe = self.db.create_recipe(
            title="김치찌개",
            description="맛있는 김치찌개 레시피",
            instructions="1. 김치를 볶는다 2. 물을 넣고 끓인다",
            author_id=self.alice.id,
            ingredients=[{"name": "김치"}, {"name": "돼지고기"}, {"name": "두부"}],
        )

    def tearDown(self):
        os.unlink(self.tmp.name)


class TestReplies(BaseTestCase):
    """Feature 11: Reply (nested comments)"""

    def test_add_reply(self):
        comment = self.db.add_comment(self.recipe.id, self.bob.id, "맛있겠다!")
        reply = self.db.add_reply(comment.id, self.alice.id, "감사합니다!")
        self.assertEqual(reply.parent_id, comment.id)
        self.assertEqual(reply.content, "감사합니다!")

    def test_get_replies(self):
        comment = self.db.add_comment(self.recipe.id, self.bob.id, "맛있겠다!")
        self.db.add_reply(comment.id, self.alice.id, "감사합니다!")
        self.db.add_reply(comment.id, self.bob.id, "다시 답글")
        replies = self.db.get_replies(comment.id)
        self.assertEqual(len(replies), 2)

    def test_reply_awards_points(self):
        comment = self.db.add_comment(self.recipe.id, self.bob.id, "맛있겠다!")
        alice_before = self.db.get_user(self.alice.id)
        self.db.add_reply(comment.id, self.alice.id, "감사합니다!")
        alice_after = self.db.get_user(self.alice.id)
        self.assertEqual(alice_after.points - alice_before.points, 1)

    def test_reply_to_nonexistent_comment(self):
        with self.assertRaises(ValueError):
            self.db.add_reply(9999, self.alice.id, "답글")

    def test_empty_reply(self):
        comment = self.db.add_comment(self.recipe.id, self.bob.id, "test")
        with self.assertRaises(ValueError):
            self.db.add_reply(comment.id, self.alice.id, "")

    def test_reply_count(self):
        comment = self.db.add_comment(self.recipe.id, self.bob.id, "test")
        self.assertEqual(self.db.get_reply_count(comment.id), 0)
        self.db.add_reply(comment.id, self.alice.id, "답글1")
        self.assertEqual(self.db.get_reply_count(comment.id), 1)


class TestUserProfile(BaseTestCase):
    """Feature 12: User profile"""

    def test_create_profile(self):
        profile = self.db.update_profile(self.alice.id, bio="요리를 좋아합니다", avatar_url="http://img.com/a.jpg")
        self.assertEqual(profile.bio, "요리를 좋아합니다")

    def test_update_profile(self):
        self.db.update_profile(self.alice.id, bio="처음")
        profile = self.db.update_profile(self.alice.id, bio="수정됨")
        self.assertEqual(profile.bio, "수정됨")

    def test_get_profile(self):
        self.db.update_profile(self.alice.id, bio="hello", website="http://example.com")
        profile = self.db.get_profile(self.alice.id)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.website, "http://example.com")

    def test_get_profile_nonexistent(self):
        profile = self.db.get_profile(self.alice.id)
        self.assertIsNone(profile)

    def test_user_detail(self):
        self.db.update_profile(self.alice.id, bio="test")
        detail = self.db.get_user_detail(self.alice.id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["username"], "alice")
        self.assertIn("badges", detail)
        self.assertIn("follower_count", detail)

    def test_user_detail_nonexistent(self):
        detail = self.db.get_user_detail(9999)
        self.assertIsNone(detail)


class TestRecipeImages(BaseTestCase):
    """Feature 13: Recipe images"""

    def test_add_image(self):
        img = self.db.add_recipe_image(self.recipe.id, "http://img.com/food.jpg", "완성 사진")
        self.assertEqual(img.image_url, "http://img.com/food.jpg")

    def test_empty_url(self):
        with self.assertRaises(ValueError):
            self.db.add_recipe_image(self.recipe.id, "")

    def test_get_images(self):
        self.db.add_recipe_image(self.recipe.id, "http://img.com/1.jpg", sort_order=1)
        self.db.add_recipe_image(self.recipe.id, "http://img.com/2.jpg", sort_order=0)
        images = self.db.get_recipe_images(self.recipe.id)
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0].sort_order, 0)  # sorted by sort_order

    def test_delete_image_by_author(self):
        img = self.db.add_recipe_image(self.recipe.id, "http://img.com/1.jpg")
        deleted = self.db.delete_recipe_image(img.id, self.alice.id)
        self.assertTrue(deleted)

    def test_delete_image_by_other(self):
        img = self.db.add_recipe_image(self.recipe.id, "http://img.com/1.jpg")
        deleted = self.db.delete_recipe_image(img.id, self.bob.id)
        self.assertFalse(deleted)


class TestNutrition(BaseTestCase):
    """Feature 14: Nutrition info"""

    def test_set_and_get(self):
        info = self.db.set_nutrition(self.recipe.id, calories=350, protein_g=20.5, carbs_g=30.0)
        self.assertEqual(info.calories, 350)
        self.assertEqual(info.protein_g, 20.5)

    def test_update_nutrition(self):
        self.db.set_nutrition(self.recipe.id, calories=350)
        info = self.db.set_nutrition(self.recipe.id, calories=400)
        self.assertEqual(info.calories, 400)

    def test_get_nonexistent(self):
        info = self.db.get_nutrition(self.recipe.id)
        self.assertIsNone(info)

    def test_all_fields(self):
        info = self.db.set_nutrition(
            self.recipe.id, calories=500, protein_g=30, carbs_g=50,
            fat_g=15, fiber_g=5, sodium_mg=800,
        )
        self.assertEqual(info.fat_g, 15)
        self.assertEqual(info.sodium_mg, 800)


class TestRecipeSteps(BaseTestCase):
    """Feature 15: Recipe steps"""

    def test_set_steps(self):
        steps = self.db.set_recipe_steps(self.recipe.id, [
            {"title": "준비", "description": "재료를 씻는다"},
            {"title": "조리", "description": "볶는다", "timer_minutes": 10},
        ])
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].step_number, 1)
        self.assertEqual(steps[1].timer_minutes, 10)

    def test_replace_steps(self):
        self.db.set_recipe_steps(self.recipe.id, [
            {"description": "step1"}, {"description": "step2"},
        ])
        self.db.set_recipe_steps(self.recipe.id, [
            {"description": "new_step1"},
        ])
        steps = self.db.get_recipe_steps(self.recipe.id)
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].description, "new_step1")

    def test_get_steps_ordered(self):
        self.db.set_recipe_steps(self.recipe.id, [
            {"description": "a"}, {"description": "b"}, {"description": "c"},
        ])
        steps = self.db.get_recipe_steps(self.recipe.id)
        self.assertEqual([s.step_number for s in steps], [1, 2, 3])

    def test_empty_steps(self):
        steps = self.db.get_recipe_steps(self.recipe.id)
        self.assertEqual(len(steps), 0)


class TestIngredientPrices(BaseTestCase):
    """Feature 16: Ingredient cost estimation"""

    def test_set_price(self):
        p = self.db.set_ingredient_price("김치", 5000, "1kg")
        self.assertEqual(p.price, 5000)

    def test_update_price(self):
        self.db.set_ingredient_price("김치", 5000)
        p = self.db.set_ingredient_price("김치", 6000)
        self.assertEqual(p.price, 6000)

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            self.db.set_ingredient_price("김치", -100)

    def test_get_price(self):
        self.db.set_ingredient_price("김치", 5000)
        p = self.db.get_ingredient_price("김치")
        self.assertIsNotNone(p)
        self.assertEqual(p.price, 5000)

    def test_get_price_nonexistent(self):
        self.assertIsNone(self.db.get_ingredient_price("없는재료"))

    def test_estimate_cost(self):
        self.db.set_ingredient_price("김치", 3000)
        self.db.set_ingredient_price("돼지고기", 8000)
        cost = self.db.estimate_recipe_cost(self.recipe.id)
        self.assertEqual(cost["total_estimated_cost"], 11000)
        self.assertEqual(len(cost["ingredients"]), 3)

    def test_estimate_partial_prices(self):
        self.db.set_ingredient_price("김치", 3000)
        cost = self.db.estimate_recipe_cost(self.recipe.id)
        self.assertEqual(cost["total_estimated_cost"], 3000)
        # 두부 has no price
        tofu = [i for i in cost["ingredients"] if i["name"] == "두부"][0]
        self.assertFalse(tofu["has_price"])


class TestBadges(BaseTestCase):
    """Feature 17: Badge/achievement system"""

    def test_all_badges_seeded(self):
        badges = self.db.get_all_badges()
        self.assertGreaterEqual(len(badges), 10)

    def test_first_recipe_badge(self):
        awarded = self.db.check_and_award_badges(self.alice.id)
        self.assertIn("first_recipe", awarded)

    def test_no_duplicate_badge(self):
        self.db.check_and_award_badges(self.alice.id)
        awarded = self.db.check_and_award_badges(self.alice.id)
        self.assertNotIn("first_recipe", awarded)

    def test_get_user_badges(self):
        self.db.check_and_award_badges(self.alice.id)
        badges = self.db.get_user_badges(self.alice.id)
        codes = [b.badge_code for b in badges]
        self.assertIn("first_recipe", codes)

    def test_points_100_badge(self):
        # Alice already has points from recipe creation
        # Add more points to reach 100
        user = self.db.get_user(self.alice.id)
        needed = 100 - user.points
        if needed > 0:
            self.db.update_points(self.alice.id, needed, "test bonus")
        awarded = self.db.check_and_award_badges(self.alice.id)
        self.assertIn("points_100", awarded)

    def test_forker_badge(self):
        self.db.fork_recipe(self.recipe.id, self.bob.id)
        awarded = self.db.check_and_award_badges(self.bob.id)
        self.assertIn("forker", awarded)


class TestRecommendations(BaseTestCase):
    """Feature 18: Recipe recommendations"""

    def test_similar_by_ingredients(self):
        recipe2 = self.db.create_recipe(
            title="김치볶음밥",
            description="볶음밥",
            instructions="볶는다",
            author_id=self.bob.id,
            ingredients=[{"name": "김치"}, {"name": "밥"}, {"name": "돼지고기"}],
        )
        similar = self.db.get_similar_recipes(self.recipe.id)
        self.assertEqual(len(similar), 1)
        self.assertEqual(similar[0].id, recipe2.id)

    def test_no_self_recommendation(self):
        similar = self.db.get_similar_recipes(self.recipe.id)
        ids = [r.id for r in similar]
        self.assertNotIn(self.recipe.id, ids)

    def test_empty_recommendations(self):
        recipe2 = self.db.create_recipe(
            title="파스타",
            description="이탈리안",
            instructions="삶는다",
            author_id=self.bob.id,
            ingredients=[{"name": "스파게티"}, {"name": "토마토소스"}],
        )
        similar = self.db.get_similar_recipes(recipe2.id)
        # No shared ingredients with 김치찌개
        for r in similar:
            self.assertNotEqual(r.id, recipe2.id)


class TestAdvancedFilter(BaseTestCase):
    """Feature 19: Advanced filtering"""

    def setUp(self):
        super().setUp()
        self.recipe2 = self.db.create_recipe(
            title="스파게티",
            description="이탈리안 파스타",
            instructions="삶아서 소스를 넣는다",
            author_id=self.bob.id,
            ingredients=[{"name": "스파게티면"}],
            cooking_time_min=20,
            difficulty="medium",
        )

    def test_filter_by_difficulty(self):
        recipes = self.db.filter_recipes(difficulty="easy")
        titles = [r.title for r in recipes]
        self.assertIn("김치찌개", titles)
        self.assertNotIn("스파게티", titles)

    def test_filter_by_max_time(self):
        recipes = self.db.filter_recipes(max_time=10)
        # 김치찌개 has cooking_time_min=0
        self.assertTrue(all(r.cooking_time_min <= 10 for r in recipes))

    def test_filter_by_tag(self):
        self.db.set_recipe_tags(self.recipe.id, ["한식"])
        recipes = self.db.filter_recipes(tag="한식")
        self.assertEqual(len(recipes), 1)

    def test_sort_by_popular(self):
        recipes = self.db.filter_recipes(sort_by="popular")
        self.assertGreaterEqual(len(recipes), 2)

    def test_filter_no_match(self):
        recipes = self.db.filter_recipes(difficulty="hard")
        self.assertEqual(len(recipes), 0)

    def test_filter_combined(self):
        recipes = self.db.filter_recipes(difficulty="easy", max_time=100)
        self.assertEqual(len(recipes), 1)


class TestCookingTimers(BaseTestCase):
    """Feature 20: Cooking timer presets"""

    def test_set_timers(self):
        timers = self.db.set_cooking_timers(self.recipe.id, [
            {"label": "끓이기", "duration_seconds": 600},
            {"label": "뜸들이기", "duration_seconds": 300},
        ])
        self.assertEqual(len(timers), 2)
        self.assertEqual(timers[0].label, "끓이기")
        self.assertEqual(timers[0].duration_seconds, 600)

    def test_replace_timers(self):
        self.db.set_cooking_timers(self.recipe.id, [
            {"label": "끓이기", "duration_seconds": 600},
        ])
        self.db.set_cooking_timers(self.recipe.id, [
            {"label": "새 타이머", "duration_seconds": 120},
        ])
        timers = self.db.get_cooking_timers(self.recipe.id)
        self.assertEqual(len(timers), 1)
        self.assertEqual(timers[0].label, "새 타이머")

    def test_get_timers_ordered(self):
        self.db.set_cooking_timers(self.recipe.id, [
            {"label": "a", "duration_seconds": 100},
            {"label": "b", "duration_seconds": 200},
            {"label": "c", "duration_seconds": 300},
        ])
        timers = self.db.get_cooking_timers(self.recipe.id)
        self.assertEqual([t.sort_order for t in timers], [0, 1, 2])

    def test_empty_timers(self):
        timers = self.db.get_cooking_timers(self.recipe.id)
        self.assertEqual(len(timers), 0)

    def test_skip_invalid_timers(self):
        timers = self.db.set_cooking_timers(self.recipe.id, [
            {"label": "", "duration_seconds": 0},  # invalid
            {"label": "valid", "duration_seconds": 60},
        ])
        self.assertEqual(len(timers), 1)


if __name__ == "__main__":
    unittest.main()
