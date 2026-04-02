"""Tests for features 21-40."""

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


class TestMealPlan(BaseTestCase):
    """Feature 21"""

    def test_set_meal_plan(self):
        plan = self.db.set_meal_plan(self.bob.id, "2026-04-01", "lunch", self.recipe.id)
        self.assertEqual(plan.date, "2026-04-01")
        self.assertEqual(plan.meal_type, "lunch")

    def test_get_meal_plans(self):
        self.db.set_meal_plan(self.bob.id, "2026-04-01", "lunch", self.recipe.id)
        self.db.set_meal_plan(self.bob.id, "2026-04-01", "dinner", self.recipe.id)
        plans = self.db.get_meal_plans(self.bob.id, "2026-04-01", "2026-04-07")
        self.assertEqual(len(plans), 2)

    def test_replace_meal_plan(self):
        self.db.set_meal_plan(self.bob.id, "2026-04-01", "lunch", self.recipe.id, "old")
        self.db.set_meal_plan(self.bob.id, "2026-04-01", "lunch", self.recipe.id, "new")
        plans = self.db.get_meal_plans(self.bob.id, "2026-04-01", "2026-04-01")
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].note, "new")

    def test_delete_meal_plan(self):
        self.db.set_meal_plan(self.bob.id, "2026-04-01", "lunch", self.recipe.id)
        deleted = self.db.delete_meal_plan(self.bob.id, "2026-04-01", "lunch")
        self.assertTrue(deleted)

    def test_invalid_meal_type(self):
        with self.assertRaises(ValueError):
            self.db.set_meal_plan(self.bob.id, "2026-04-01", "brunch", self.recipe.id)


class TestShoppingList(BaseTestCase):
    """Feature 22"""

    def test_add_item(self):
        item = self.db.add_shopping_item(self.bob.id, "양파", "2", "개")
        self.assertEqual(item.name, "양파")

    def test_add_from_recipe(self):
        items = self.db.add_recipe_to_shopping(self.bob.id, self.recipe.id)
        self.assertEqual(len(items), 3)

    def test_get_list(self):
        self.db.add_shopping_item(self.bob.id, "양파")
        items = self.db.get_shopping_list(self.bob.id)
        self.assertEqual(len(items), 1)

    def test_toggle_checked(self):
        item = self.db.add_shopping_item(self.bob.id, "양파")
        self.db.toggle_shopping_item(item.id, self.bob.id)
        items = self.db.get_shopping_list(self.bob.id)
        self.assertTrue(items[0].checked)

    def test_clear_checked_only(self):
        i1 = self.db.add_shopping_item(self.bob.id, "양파")
        self.db.add_shopping_item(self.bob.id, "마늘")
        self.db.toggle_shopping_item(i1.id, self.bob.id)
        removed = self.db.clear_shopping_list(self.bob.id, checked_only=True)
        self.assertEqual(removed, 1)
        self.assertEqual(len(self.db.get_shopping_list(self.bob.id)), 1)

    def test_empty_name(self):
        with self.assertRaises(ValueError):
            self.db.add_shopping_item(self.bob.id, "")


class TestBlockUser(BaseTestCase):
    """Feature 23"""

    def test_block(self):
        result = self.db.block_user(self.alice.id, self.bob.id)
        self.assertTrue(result["blocked"])

    def test_block_self(self):
        with self.assertRaises(ValueError):
            self.db.block_user(self.alice.id, self.alice.id)

    def test_double_block(self):
        self.db.block_user(self.alice.id, self.bob.id)
        with self.assertRaises(ValueError):
            self.db.block_user(self.alice.id, self.bob.id)

    def test_unblock(self):
        self.db.block_user(self.alice.id, self.bob.id)
        self.assertTrue(self.db.unblock_user(self.alice.id, self.bob.id))
        self.assertFalse(self.db.is_blocked(self.alice.id, self.bob.id))

    def test_block_removes_follow(self):
        self.db.toggle_follow(self.alice.id, self.bob.id)
        self.db.block_user(self.alice.id, self.bob.id)
        self.assertFalse(self.db.is_following(self.alice.id, self.bob.id))

    def test_get_blocked(self):
        self.db.block_user(self.alice.id, self.bob.id)
        blocked = self.db.get_blocked_users(self.alice.id)
        self.assertEqual(len(blocked), 1)


class TestQA(BaseTestCase):
    """Feature 24"""

    def test_ask_question(self):
        qa = self.db.ask_question(self.recipe.id, self.bob.id, "얼마나 끓여야 하나요?")
        self.assertEqual(qa.question, "얼마나 끓여야 하나요?")

    def test_answer_question(self):
        qa = self.db.ask_question(self.recipe.id, self.bob.id, "질문")
        answered = self.db.answer_question(qa.id, self.alice.id, "30분이요")
        self.assertEqual(answered.answer, "30분이요")

    def test_answer_awards_points(self):
        qa = self.db.ask_question(self.recipe.id, self.bob.id, "질문")
        before = self.db.get_user(self.alice.id).points
        self.db.answer_question(qa.id, self.alice.id, "답변")
        after = self.db.get_user(self.alice.id).points
        self.assertEqual(after - before, 2)

    def test_get_qa(self):
        self.db.ask_question(self.recipe.id, self.bob.id, "Q1")
        self.db.ask_question(self.recipe.id, self.bob.id, "Q2")
        qas = self.db.get_recipe_qa(self.recipe.id)
        self.assertEqual(len(qas), 2)

    def test_empty_question(self):
        with self.assertRaises(ValueError):
            self.db.ask_question(self.recipe.id, self.bob.id, "")


class TestSeason(BaseTestCase):
    """Feature 25"""

    def test_set_season(self):
        self.assertTrue(self.db.set_recipe_season(self.recipe.id, "winter"))

    def test_get_seasonal(self):
        self.db.set_recipe_season(self.recipe.id, "winter")
        recipes = self.db.get_seasonal_recipes("winter")
        self.assertEqual(len(recipes), 1)

    def test_all_season_included(self):
        self.db.set_recipe_season(self.recipe.id, "all")
        recipes = self.db.get_seasonal_recipes("summer")
        self.assertEqual(len(recipes), 1)

    def test_invalid_season(self):
        with self.assertRaises(ValueError):
            self.db.set_recipe_season(self.recipe.id, "rainy")


class TestAllergyInfo(BaseTestCase):
    """Feature 26"""

    def test_set_allergens(self):
        result = self.db.set_allergens(self.recipe.id, ["soy", "gluten"])
        self.assertEqual(len(result), 2)

    def test_get_allergens(self):
        self.db.set_allergens(self.recipe.id, ["soy"])
        allergens = self.db.get_allergens(self.recipe.id)
        self.assertIn("soy", allergens)

    def test_find_without_allergens(self):
        self.db.set_allergens(self.recipe.id, ["soy"])
        recipe2 = self.db.create_recipe(
            title="파스타", description="", instructions="ok",
            author_id=self.bob.id, ingredients=[{"name": "면"}],
        )
        recipes = self.db.find_recipes_without_allergens(["soy"])
        ids = [r.id for r in recipes]
        self.assertNotIn(self.recipe.id, ids)
        self.assertIn(recipe2.id, ids)


class TestDifficultyVote(BaseTestCase):
    """Feature 27"""

    def test_vote(self):
        result = self.db.vote_difficulty(self.recipe.id, self.bob.id, "hard")
        self.assertEqual(result["your_vote"], "hard")
        self.assertEqual(result["distribution"]["hard"], 1)

    def test_change_vote(self):
        self.db.vote_difficulty(self.recipe.id, self.bob.id, "easy")
        result = self.db.vote_difficulty(self.recipe.id, self.bob.id, "hard")
        self.assertEqual(result["distribution"]["hard"], 1)
        self.assertEqual(result["distribution"]["easy"], 0)

    def test_invalid_vote(self):
        with self.assertRaises(ValueError):
            self.db.vote_difficulty(self.recipe.id, self.bob.id, "impossible")

    def test_get_votes(self):
        self.db.vote_difficulty(self.recipe.id, self.bob.id, "easy")
        result = self.db.get_difficulty_votes(self.recipe.id)
        self.assertEqual(result["total_votes"], 1)


class TestRecipeCompare(BaseTestCase):
    """Feature 28"""

    def test_compare(self):
        recipe2 = self.db.create_recipe(
            title="된장찌개", description="", instructions="ok",
            author_id=self.bob.id,
            ingredients=[{"name": "된장"}, {"name": "두부"}],
        )
        result = self.db.compare_recipes(self.recipe.id, recipe2.id)
        self.assertIn("두부", result["shared_ingredients"])
        self.assertIn("김치", result["only_in_a"])
        self.assertIn("된장", result["only_in_b"])

    def test_compare_nonexistent(self):
        with self.assertRaises(ValueError):
            self.db.compare_recipes(self.recipe.id, 9999)


class TestUserStats(BaseTestCase):
    """Feature 29"""

    def test_stats(self):
        stats = self.db.get_user_stats(self.alice.id)
        self.assertEqual(stats["recipes"], 1)
        self.assertIn("level", stats)
        self.assertIn("points", stats)


class TestViewHistory(BaseTestCase):
    """Feature 30"""

    def test_record_view(self):
        self.db.record_view(self.bob.id, self.recipe.id)
        history = self.db.get_view_history(self.bob.id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["recipe_id"], self.recipe.id)

    def test_view_increments_count(self):
        self.db.record_view(self.bob.id, self.recipe.id)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.view_count, 1)

    def test_multiple_views(self):
        self.db.record_view(self.bob.id, self.recipe.id)
        self.db.record_view(self.bob.id, self.recipe.id)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.view_count, 2)


class TestIngredientSub(BaseTestCase):
    """Feature 31"""

    def test_add_substitution(self):
        sub = self.db.add_substitution("버터", "코코넛 오일", "비건용")
        self.assertEqual(sub.original, "버터")

    def test_get_subs(self):
        self.db.add_substitution("버터", "코코넛 오일")
        self.db.add_substitution("버터", "마가린")
        subs = self.db.get_substitutions("버터")
        self.assertEqual(len(subs), 2)

    def test_duplicate_sub(self):
        self.db.add_substitution("버터", "코코넛 오일")
        with self.assertRaises(ValueError):
            self.db.add_substitution("버터", "코코넛 오일")


class TestChallenge(BaseTestCase):
    """Feature 32"""

    def test_create_challenge(self):
        ch = self.db.create_challenge("김치 챌린지", "김치로 요리하세요", "김치", "2026-04-01", "2026-04-07")
        self.assertEqual(ch.title, "김치 챌린지")

    def test_enter_challenge(self):
        ch = self.db.create_challenge("챌린지", "", "", "2026-04-01", "2026-04-07")
        result = self.db.enter_challenge(ch.id, self.bob.id, self.recipe.id)
        self.assertTrue(result["entered"])

    def test_double_entry(self):
        ch = self.db.create_challenge("챌린지", "", "", "2026-04-01", "2026-04-07")
        self.db.enter_challenge(ch.id, self.bob.id, self.recipe.id)
        with self.assertRaises(ValueError):
            self.db.enter_challenge(ch.id, self.bob.id, self.recipe.id)

    def test_challenge_awards_points(self):
        ch = self.db.create_challenge("챌린지", "", "", "2026-04-01", "2026-04-07")
        before = self.db.get_user(self.bob.id).points
        self.db.enter_challenge(ch.id, self.bob.id, self.recipe.id)
        after = self.db.get_user(self.bob.id).points
        self.assertEqual(after - before, 5)

    def test_get_entries(self):
        ch = self.db.create_challenge("챌린지", "", "", "2026-04-01", "2026-04-07")
        self.db.enter_challenge(ch.id, self.bob.id, self.recipe.id)
        entries = self.db.get_challenge_entries(ch.id)
        self.assertEqual(len(entries), 1)

    def test_active_challenges(self):
        self.db.create_challenge("활성", "", "", "2026-04-01", "2026-04-30")
        self.db.create_challenge("지난", "", "", "2025-01-01", "2025-01-07")
        active = self.db.get_active_challenges("2026-04-02")
        self.assertEqual(len(active), 1)


class TestPoll(BaseTestCase):
    """Feature 33"""

    def test_create_poll(self):
        result = self.db.create_poll(self.recipe.id, self.alice.id, "어떤 김치?", ["배추김치", "열무김치"])
        self.assertIn("poll_id", result)
        self.assertEqual(len(result["options"]), 2)

    def test_vote_poll(self):
        poll = self.db.create_poll(self.recipe.id, self.alice.id, "Q?", ["A", "B"])
        opt_id = poll["options"][0]["id"]
        result = self.db.vote_poll(poll["poll_id"], opt_id, self.bob.id)
        voted = [o for o in result["options"] if o["id"] == opt_id][0]
        self.assertEqual(voted["vote_count"], 1)

    def test_double_vote(self):
        poll = self.db.create_poll(self.recipe.id, self.alice.id, "Q?", ["A", "B"])
        opt_id = poll["options"][0]["id"]
        self.db.vote_poll(poll["poll_id"], opt_id, self.bob.id)
        with self.assertRaises(ValueError):
            self.db.vote_poll(poll["poll_id"], opt_id, self.bob.id)

    def test_get_poll(self):
        poll = self.db.create_poll(self.recipe.id, self.alice.id, "Q?", ["A", "B"])
        fetched = self.db.get_poll(poll["poll_id"])
        self.assertEqual(fetched["question"], "Q?")


class TestUserLevel(BaseTestCase):
    """Feature 34"""

    def test_level(self):
        result = self.db.get_user_level(self.alice.id)
        self.assertIn("level", result)
        self.assertIn("points_to_next", result)

    def test_level_progression(self):
        self.db.update_points(self.alice.id, 500, "test")
        result = self.db.get_user_level(self.alice.id)
        self.assertEqual(result["level"], "마스터 셰프")

    def test_nonexistent_user(self):
        with self.assertRaises(ValueError):
            self.db.get_user_level(9999)


class TestRecipeTips(BaseTestCase):
    """Feature 35"""

    def test_add_tip(self):
        tip = self.db.add_recipe_tip(self.recipe.id, self.bob.id, "김치는 신 김치가 더 맛있어요")
        self.assertEqual(tip.content, "김치는 신 김치가 더 맛있어요")

    def test_get_tips(self):
        self.db.add_recipe_tip(self.recipe.id, self.bob.id, "팁1")
        self.db.add_recipe_tip(self.recipe.id, self.alice.id, "팁2")
        tips = self.db.get_recipe_tips(self.recipe.id)
        self.assertEqual(len(tips), 2)

    def test_empty_tip(self):
        with self.assertRaises(ValueError):
            self.db.add_recipe_tip(self.recipe.id, self.bob.id, "")


class TestExport(BaseTestCase):
    """Feature 36"""

    def test_export_json(self):
        data = self.db.export_recipe(self.recipe.id, "json")
        self.assertEqual(data["title"], "김치찌개")
        self.assertEqual(len(data["ingredients"]), 3)

    def test_export_text(self):
        text = self.db.export_recipe(self.recipe.id, "text")
        self.assertIn("김치찌개", text)
        self.assertIn("김치", text)

    def test_export_nonexistent(self):
        with self.assertRaises(ValueError):
            self.db.export_recipe(9999)


class TestRecipeVersions(BaseTestCase):
    """Feature 37"""

    def test_save_version(self):
        ver = self.db.save_recipe_version(self.recipe.id)
        self.assertEqual(ver.version_num, 1)
        self.assertEqual(ver.title, "김치찌개")

    def test_multiple_versions(self):
        self.db.save_recipe_version(self.recipe.id)
        ver2 = self.db.save_recipe_version(self.recipe.id)
        self.assertEqual(ver2.version_num, 2)

    def test_get_versions(self):
        self.db.save_recipe_version(self.recipe.id)
        self.db.save_recipe_version(self.recipe.id)
        versions = self.db.get_recipe_versions(self.recipe.id)
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version_num, 2)  # newest first


class TestBookmarkTags(BaseTestCase):
    """Feature 38"""

    def test_create_tag(self):
        tag = self.db.create_bookmark_tag(self.bob.id, "한식")
        self.assertEqual(tag.name, "한식")

    def test_duplicate_tag(self):
        self.db.create_bookmark_tag(self.bob.id, "한식")
        with self.assertRaises(ValueError):
            self.db.create_bookmark_tag(self.bob.id, "한식")

    def test_tag_bookmark(self):
        tag = self.db.create_bookmark_tag(self.bob.id, "한식")
        self.db.toggle_bookmark(self.bob.id, self.recipe.id)
        self.db.tag_bookmark(self.bob.id, self.recipe.id, tag.id)
        recipes = self.db.get_bookmarks_by_tag(self.bob.id, tag.id)
        self.assertEqual(len(recipes), 1)

    def test_tag_unbookmarked(self):
        tag = self.db.create_bookmark_tag(self.bob.id, "한식")
        with self.assertRaises(ValueError):
            self.db.tag_bookmark(self.bob.id, self.recipe.id, tag.id)


class TestPrintFormat(BaseTestCase):
    """Feature 39"""

    def test_print(self):
        data = self.db.get_print_format(self.recipe.id)
        self.assertIsNotNone(data)
        self.assertEqual(data["title"], "김치찌개")
        self.assertEqual(len(data["ingredients"]), 3)

    def test_print_nonexistent(self):
        self.assertIsNone(self.db.get_print_format(9999))


class TestDuplicateDetection(BaseTestCase):
    """Feature 40"""

    def test_find_duplicates(self):
        recipe2 = self.db.create_recipe(
            title="김치찌개 레시피", description="", instructions="ok",
            author_id=self.bob.id,
            ingredients=[{"name": "김치"}, {"name": "돼지고기"}, {"name": "두부"}],
        )
        dupes = self.db.find_duplicates(self.recipe.id, threshold=0.5)
        self.assertGreaterEqual(len(dupes), 1)
        self.assertEqual(dupes[0]["recipe_id"], recipe2.id)

    def test_no_self_duplicate(self):
        dupes = self.db.find_duplicates(self.recipe.id, threshold=0.0)
        ids = [d["recipe_id"] for d in dupes]
        self.assertNotIn(self.recipe.id, ids)

    def test_low_similarity_excluded(self):
        self.db.create_recipe(
            title="파스타", description="", instructions="ok",
            author_id=self.bob.id,
            ingredients=[{"name": "스파게티면"}, {"name": "토마토소스"}],
        )
        dupes = self.db.find_duplicates(self.recipe.id, threshold=0.7)
        # Pasta should not match kimchi jjigae
        self.assertEqual(len(dupes), 0)


if __name__ == "__main__":
    unittest.main()
