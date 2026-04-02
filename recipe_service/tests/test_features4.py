"""Tests for features 41-70."""

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
            description="맛있는 김치찌개",
            instructions="끓인다",
            author_id=self.alice.id,
            ingredients=[{"name": "김치"}, {"name": "돼지고기"}, {"name": "두부"}],
        )

    def tearDown(self):
        os.unlink(self.tmp.name)


class TestRecipeCategory(BaseTestCase):
    """Feature 41"""

    def test_set_category(self):
        result = self.db.set_recipe_category(self.recipe.id, "korean")
        self.assertTrue(result)

    def test_category_persists(self):
        self.db.set_recipe_category(self.recipe.id, "korean")
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.category, "korean")

    def test_change_category(self):
        self.db.set_recipe_category(self.recipe.id, "korean")
        self.db.set_recipe_category(self.recipe.id, "chinese")
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.category, "chinese")


class TestEquipment(BaseTestCase):
    """Feature 42"""

    def test_set_equipment(self):
        equip = self.db.set_equipment(self.recipe.id, ["냄비", "칼"])
        self.assertEqual(len(equip), 2)
        self.assertIn("냄비", equip)

    def test_get_equipment(self):
        self.db.set_equipment(self.recipe.id, ["냄비", "칼"])
        equip = self.db.get_equipment(self.recipe.id)
        self.assertEqual(len(equip), 2)

    def test_replace_equipment(self):
        self.db.set_equipment(self.recipe.id, ["냄비", "칼"])
        self.db.set_equipment(self.recipe.id, ["프라이팬"])
        equip = self.db.get_equipment(self.recipe.id)
        self.assertEqual(equip, ["프라이팬"])


class TestAutoDifficulty(BaseTestCase):
    """Feature 43"""

    def test_calculate_difficulty(self):
        difficulty = self.db.calculate_difficulty(self.recipe.id)
        self.assertIn(difficulty, ["easy", "medium", "hard"])

    def test_nonexistent_recipe(self):
        with self.assertRaises(ValueError):
            self.db.calculate_difficulty(9999)


class TestBookmarkSorting(BaseTestCase):
    """Feature 44"""

    def test_sorted_by_recent(self):
        r2 = self.db.create_recipe(
            title="비빔밥", description="", instructions="섞는다",
            author_id=self.alice.id, ingredients=[{"name": "밥"}],
        )
        self.db.toggle_bookmark(self.bob.id, self.recipe.id)
        time.sleep(0.05)
        self.db.toggle_bookmark(self.bob.id, r2.id)
        recipes = self.db.get_user_bookmarks_sorted(self.bob.id, sort_by="recent")
        self.assertEqual(len(recipes), 2)

    def test_sorted_by_title(self):
        r2 = self.db.create_recipe(
            title="비빔밥", description="", instructions="섞는다",
            author_id=self.alice.id, ingredients=[{"name": "밥"}],
        )
        self.db.toggle_bookmark(self.bob.id, self.recipe.id)
        self.db.toggle_bookmark(self.bob.id, r2.id)
        recipes = self.db.get_user_bookmarks_sorted(self.bob.id, sort_by="title")
        self.assertEqual(len(recipes), 2)


class TestCloneRecipe(BaseTestCase):
    """Feature 45"""

    def test_clone(self):
        cloned = self.db.clone_recipe(self.recipe.id, self.alice.id)
        self.assertEqual(cloned.author_id, self.alice.id)
        self.assertIn("복사", cloned.title)

    def test_clone_has_ingredients(self):
        cloned = self.db.clone_recipe(self.recipe.id, self.alice.id)
        ings = self.db.get_recipe_ingredients(cloned.id)
        self.assertEqual(len(ings), 3)

    def test_clone_nonexistent(self):
        with self.assertRaises(ValueError):
            self.db.clone_recipe(9999, self.alice.id)


class TestUserNotes(BaseTestCase):
    """Feature 46"""

    def test_set_note(self):
        note = self.db.set_user_note(self.bob.id, self.recipe.id, "맛있었다")
        self.assertEqual(note.content, "맛있었다")

    def test_get_note(self):
        self.db.set_user_note(self.bob.id, self.recipe.id, "맛있었다")
        note = self.db.get_user_note(self.bob.id, self.recipe.id)
        self.assertIsNotNone(note)
        self.assertEqual(note.content, "맛있었다")

    def test_update_note(self):
        self.db.set_user_note(self.bob.id, self.recipe.id, "맛있었다")
        self.db.set_user_note(self.bob.id, self.recipe.id, "아주 맛있었다")
        note = self.db.get_user_note(self.bob.id, self.recipe.id)
        self.assertEqual(note.content, "아주 맛있었다")

    def test_no_note(self):
        note = self.db.get_user_note(self.bob.id, self.recipe.id)
        self.assertIsNone(note)


class TestUnitConversion(BaseTestCase):
    """Feature 47"""

    def test_tbsp_to_ml(self):
        result = Database.convert_unit(2, "tbsp", "ml")
        self.assertIsNotNone(result)
        self.assertGreater(result, 25.0)

    def test_invalid_conversion(self):
        result = Database.convert_unit(1, "kg", "ml")
        self.assertIsNone(result)


class TestScaleRecipe(BaseTestCase):
    """Feature 48"""

    def test_scale_up(self):
        result = self.db.scale_recipe(self.recipe.id, 4)
        self.assertEqual(result["target_servings"], 4)
        self.assertIn("ingredients", result)

    def test_scale_nonexistent(self):
        with self.assertRaises(ValueError):
            self.db.scale_recipe(9999, 2)


class TestRecipeVisibility(BaseTestCase):
    """Feature 49"""

    def test_set_private(self):
        result = self.db.set_recipe_visibility(self.recipe.id, self.alice.id, False)
        self.assertTrue(result)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertFalse(recipe.is_public)

    def test_wrong_user(self):
        result = self.db.set_recipe_visibility(self.recipe.id, self.bob.id, False)
        self.assertFalse(result)


class TestSearchHistory(BaseTestCase):
    """Feature 50"""

    def test_record_and_get(self):
        self.db.record_search(self.alice.id, "김치")
        self.db.record_search(self.alice.id, "비빔밥")
        history = self.db.get_search_history(self.alice.id)
        self.assertEqual(len(history), 2)

    def test_clear(self):
        self.db.record_search(self.alice.id, "김치")
        count = self.db.clear_search_history(self.alice.id)
        self.assertEqual(count, 1)
        self.assertEqual(len(self.db.get_search_history(self.alice.id)), 0)


class TestAutocomplete(BaseTestCase):
    """Feature 51"""

    def test_autocomplete(self):
        results = self.db.autocomplete_ingredient("김", limit=10)
        self.assertIn("김치", results)

    def test_no_match(self):
        results = self.db.autocomplete_ingredient("zzz", limit=10)
        self.assertEqual(len(results), 0)


class TestScheduledPublishing(BaseTestCase):
    """Feature 52"""

    def test_schedule(self):
        future = time.time() + 86400
        result = self.db.schedule_recipe(self.recipe.id, self.alice.id, future)
        self.assertTrue(result)

    def test_publish_scheduled(self):
        past = time.time() - 100
        self.db.schedule_recipe(self.recipe.id, self.alice.id, past)
        count = self.db.publish_scheduled_recipes()
        self.assertGreaterEqual(count, 0)

    def test_schedule_wrong_user(self):
        result = self.db.schedule_recipe(self.recipe.id, self.bob.id, time.time() + 86400)
        self.assertFalse(result)


class TestActivityLog(BaseTestCase):
    """Feature 53"""

    def test_log_and_get(self):
        self.db.log_activity(self.alice.id, "create_recipe", "김치찌개")
        logs = self.db.get_activity_log(self.alice.id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "create_recipe")

    def test_multiple_logs(self):
        self.db.log_activity(self.alice.id, "create_recipe")
        self.db.log_activity(self.alice.id, "like_recipe")
        logs = self.db.get_activity_log(self.alice.id, limit=50)
        self.assertEqual(len(logs), 2)


class TestFreshnessScore(BaseTestCase):
    """Feature 54"""

    def test_freshness(self):
        result = self.db.get_freshness_score(self.recipe.id)
        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0)


class TestFollowersOnlyRecipes(BaseTestCase):
    """Feature 55"""

    def test_followers_only(self):
        self.db.set_recipe_visibility(self.recipe.id, self.alice.id, False)
        self.db.toggle_follow(self.bob.id, self.alice.id)
        recipes = self.db.get_followers_only_recipes(self.bob.id, self.alice.id)
        self.assertIsInstance(recipes, list)


class TestCuratedLists(BaseTestCase):
    """Feature 56"""

    def test_create_list(self):
        cl = self.db.create_curated_list(self.alice.id, "베스트 레시피")
        self.assertEqual(cl.title, "베스트 레시피")

    def test_add_recipe(self):
        cl = self.db.create_curated_list(self.alice.id, "베스트")
        self.db.add_to_curated_list(cl.id, self.recipe.id)
        recipes = self.db.get_curated_list_recipes(cl.id)
        self.assertEqual(len(recipes), 1)

    def test_get_all_lists(self):
        self.db.create_curated_list(self.alice.id, "리스트1")
        self.db.create_curated_list(self.bob.id, "리스트2")
        lists = self.db.get_all_curated_lists()
        self.assertEqual(len(lists), 2)


class TestLikeTimeline(BaseTestCase):
    """Feature 57"""

    def test_timeline(self):
        self.db.toggle_like(self.bob.id, self.recipe.id)
        timeline = self.db.get_like_timeline(self.bob.id)
        self.assertEqual(len(timeline), 1)


class TestIngredientNutrition(BaseTestCase):
    """Feature 58"""

    def test_set_and_get(self):
        info = self.db.set_ingredient_nutrition("김치", calories=20, protein=2, carbs=3, fat=0.5)
        self.assertEqual(info.name, "김치")
        got = self.db.get_ingredient_nutrition("김치")
        self.assertIsNotNone(got)
        self.assertAlmostEqual(got.calories_per_100g, 20)

    def test_not_found(self):
        self.assertIsNone(self.db.get_ingredient_nutrition("unknown"))


class TestTrendingTags(BaseTestCase):
    """Feature 59"""

    def test_trending(self):
        self.db.set_recipe_tags(self.recipe.id, ["매운맛", "한식"])
        tags = self.db.get_trending_tags(days=30, limit=5)
        self.assertIsInstance(tags, list)


class TestUserPreferences(BaseTestCase):
    """Feature 60"""

    def test_set_and_get(self):
        self.db.set_user_preferences(self.alice.id, ["korean"], ["땅콩"], 30)
        pref = self.db.get_user_preferences(self.alice.id)
        self.assertIsNotNone(pref)

    def test_personalized(self):
        self.db.set_user_preferences(self.alice.id, ["korean"], [], 120)
        self.db.set_recipe_category(self.recipe.id, "korean")
        recipes = self.db.get_personalized_recipes(self.alice.id)
        self.assertIsInstance(recipes, list)


class TestRecipeTranslation(BaseTestCase):
    """Feature 61"""

    def test_set_translation(self):
        t = self.db.set_translation(self.recipe.id, "en", "Kimchi Stew", "Delicious kimchi stew")
        self.assertEqual(t.language, "en")

    def test_get_translations(self):
        self.db.set_translation(self.recipe.id, "en", "Kimchi Stew")
        self.db.set_translation(self.recipe.id, "ja", "キムチチゲ")
        ts = self.db.get_translations(self.recipe.id)
        self.assertEqual(len(ts), 2)

    def test_update_translation(self):
        self.db.set_translation(self.recipe.id, "en", "Old Title")
        self.db.set_translation(self.recipe.id, "en", "New Title")
        ts = self.db.get_translations(self.recipe.id)
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0].title, "New Title")


class TestPantry(BaseTestCase):
    """Feature 62"""

    def test_add_pantry_item(self):
        item = self.db.add_pantry_item(self.alice.id, "김치", "500", "g")
        self.assertEqual(item.name, "김치")

    def test_get_pantry(self):
        self.db.add_pantry_item(self.alice.id, "김치")
        self.db.add_pantry_item(self.alice.id, "두부")
        items = self.db.get_pantry(self.alice.id)
        self.assertEqual(len(items), 2)

    def test_delete_pantry_item(self):
        item = self.db.add_pantry_item(self.alice.id, "김치")
        self.assertTrue(self.db.delete_pantry_item(item.id, self.alice.id))
        self.assertEqual(len(self.db.get_pantry(self.alice.id)), 0)

    def test_find_recipes_from_pantry(self):
        self.db.add_pantry_item(self.alice.id, "김치")
        self.db.add_pantry_item(self.alice.id, "돼지고기")
        results = self.db.find_recipes_from_pantry(self.alice.id, min_match=0.3)
        self.assertIsInstance(results, list)


class TestShareStats(BaseTestCase):
    """Feature 63"""

    def test_share_stats(self):
        self.db.create_share_link(self.recipe.id)
        stats = self.db.get_share_stats(self.recipe.id)
        self.assertIn("has_share_link", stats)
        self.assertTrue(stats["has_share_link"])


class TestRecommendationsWithReasons(BaseTestCase):
    """Feature 64"""

    def test_recommendations(self):
        r2 = self.db.create_recipe(
            title="된장찌개", description="", instructions="끓인다",
            author_id=self.alice.id, ingredients=[{"name": "된장"}, {"name": "두부"}],
        )
        recs = self.db.get_recommendations_with_reasons(self.recipe.id)
        self.assertIsInstance(recs, list)


class TestNotificationPrefs(BaseTestCase):
    """Feature 65"""

    def test_set_and_get(self):
        self.db.set_notification_prefs(self.alice.id, likes=True, comments=False, follows=True, challenges=False)
        pref = self.db.get_notification_prefs(self.alice.id)
        self.assertTrue(pref.likes)
        self.assertFalse(pref.comments)

    def test_default_prefs(self):
        pref = self.db.get_notification_prefs(self.alice.id)
        self.assertTrue(pref.likes)
        self.assertTrue(pref.comments)


class TestAttemptLogs(BaseTestCase):
    """Feature 66"""

    def test_log_attempt(self):
        log = self.db.log_attempt(self.bob.id, self.recipe.id, "success", "잘됐다")
        self.assertEqual(log.status, "success")

    def test_get_attempts(self):
        self.db.log_attempt(self.bob.id, self.recipe.id, "success")
        self.db.log_attempt(self.bob.id, self.recipe.id, "failed")
        logs = self.db.get_attempt_logs(self.bob.id)
        self.assertEqual(len(logs), 2)

    def test_filter_by_recipe(self):
        r2 = self.db.create_recipe(
            title="비빔밥", description="", instructions="섞는다",
            author_id=self.alice.id, ingredients=[{"name": "밥"}],
        )
        self.db.log_attempt(self.bob.id, self.recipe.id, "success")
        self.db.log_attempt(self.bob.id, r2.id, "failed")
        logs = self.db.get_attempt_logs(self.bob.id, recipe_id=self.recipe.id)
        self.assertEqual(len(logs), 1)


class TestPopularSearches(BaseTestCase):
    """Feature 67"""

    def test_popular(self):
        self.db.record_search(self.alice.id, "김치")
        self.db.record_search(self.bob.id, "김치")
        self.db.record_search(self.alice.id, "비빔밥")
        results = self.db.get_popular_searches(limit=10)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)


class TestRecipeQuiz(BaseTestCase):
    """Feature 68"""

    def test_create_quiz(self):
        quiz = self.db.create_quiz(self.recipe.id, "김치찌개에 넣는 재료는?", "김치", ["밀가루", "초콜릿"])
        self.assertEqual(quiz.question, "김치찌개에 넣는 재료는?")

    def test_get_quizzes(self):
        self.db.create_quiz(self.recipe.id, "질문1", "정답1", ["오답1"])
        quizzes = self.db.get_recipe_quizzes(self.recipe.id)
        self.assertEqual(len(quizzes), 1)

    def test_check_correct_answer(self):
        quiz = self.db.create_quiz(self.recipe.id, "질문", "정답", ["오답"])
        result = self.db.check_quiz_answer(quiz.id, "정답")
        self.assertTrue(result["correct"])

    def test_check_wrong_answer(self):
        quiz = self.db.create_quiz(self.recipe.id, "질문", "정답", ["오답"])
        result = self.db.check_quiz_answer(quiz.id, "오답")
        self.assertFalse(result["correct"])


class TestHealthGoals(BaseTestCase):
    """Feature 69-70"""

    def test_set_and_get(self):
        self.db.set_health_goal(self.alice.id, daily_calories=2000, daily_protein_g=50)
        goal = self.db.get_health_goal(self.alice.id)
        self.assertIsNotNone(goal)
        self.assertEqual(goal.daily_calories, 2000)

    def test_no_goal(self):
        goal = self.db.get_health_goal(self.alice.id)
        self.assertIsNone(goal)

    def test_meal_plan_nutrition(self):
        self.db.set_health_goal(self.alice.id, daily_calories=2000)
        self.db.set_nutrition(self.recipe.id, calories=500, protein_g=20)
        self.db.set_meal_plan(self.alice.id, "2026-04-01", "lunch", self.recipe.id)
        result = self.db.check_meal_plan_nutrition(self.alice.id, "2026-04-01")
        self.assertIn("consumed", result)


if __name__ == "__main__":
    unittest.main()
