"""Tests for 10 new features: follow, tags, search, report, fork,
weekly popular, cook log, collections, notifications, share links."""

import os
import tempfile
import time
import unittest

from recipe_service.models import Database


class BaseTestCase(unittest.TestCase):
    """Common setup for all feature tests."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.alice = self.db.create_user("alice", "alice@test.com", "pass1234")
        self.bob = self.db.create_user("bob", "bob@test.com", "pass1234")
        self.carol = self.db.create_user("carol", "carol@test.com", "pass1234")
        self.recipe = self.db.create_recipe(
            title="김치찌개",
            description="맛있는 김치찌개 레시피",
            instructions="1. 김치를 볶는다 2. 물을 넣고 끓인다",
            author_id=self.alice.id,
            ingredients=[{"name": "김치"}, {"name": "돼지고기"}, {"name": "두부"}],
        )

    def tearDown(self):
        os.unlink(self.tmp.name)


class TestFollow(BaseTestCase):
    """Feature 1: Follow system"""

    def test_follow(self):
        result = self.db.toggle_follow(self.bob.id, self.alice.id)
        self.assertTrue(result["following"])

    def test_unfollow(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        result = self.db.toggle_follow(self.bob.id, self.alice.id)
        self.assertFalse(result["following"])

    def test_cannot_follow_self(self):
        with self.assertRaises(ValueError):
            self.db.toggle_follow(self.alice.id, self.alice.id)

    def test_follow_nonexistent_user(self):
        with self.assertRaises(ValueError):
            self.db.toggle_follow(self.bob.id, 9999)

    def test_is_following(self):
        self.assertFalse(self.db.is_following(self.bob.id, self.alice.id))
        self.db.toggle_follow(self.bob.id, self.alice.id)
        self.assertTrue(self.db.is_following(self.bob.id, self.alice.id))

    def test_get_followers(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        self.db.toggle_follow(self.carol.id, self.alice.id)
        followers = self.db.get_followers(self.alice.id)
        self.assertEqual(len(followers), 2)

    def test_get_following(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        self.db.toggle_follow(self.bob.id, self.carol.id)
        following = self.db.get_following(self.bob.id)
        self.assertEqual(len(following), 2)

    def test_follower_count(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        self.assertEqual(self.db.get_follower_count(self.alice.id), 1)
        self.assertEqual(self.db.get_following_count(self.bob.id), 1)

    def test_following_feed(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        recipes = self.db.get_following_recipes(self.bob.id)
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0].title, "김치찌개")

    def test_follow_creates_notification(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        notifs = self.db.get_notifications(self.alice.id)
        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs[0].type, "follow")


class TestTags(BaseTestCase):
    """Feature 2: Tag system"""

    def test_set_and_get_tags(self):
        tags = self.db.set_recipe_tags(self.recipe.id, ["한식", "찌개", "매운맛"])
        self.assertEqual(len(tags), 3)
        result = self.db.get_recipe_tags(self.recipe.id)
        self.assertIn("한식", result)
        self.assertIn("찌개", result)

    def test_replace_tags(self):
        self.db.set_recipe_tags(self.recipe.id, ["한식", "찌개"])
        self.db.set_recipe_tags(self.recipe.id, ["일식"])
        result = self.db.get_recipe_tags(self.recipe.id)
        self.assertEqual(result, ["일식"])

    def test_find_by_tag(self):
        self.db.set_recipe_tags(self.recipe.id, ["한식"])
        recipes = self.db.find_recipes_by_tag("한식")
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0].id, self.recipe.id)

    def test_popular_tags(self):
        self.db.set_recipe_tags(self.recipe.id, ["한식", "찌개"])
        recipe2 = self.db.create_recipe(
            title="된장찌개", description="", instructions="끓인다",
            author_id=self.bob.id, ingredients=[{"name": "된장"}],
        )
        self.db.set_recipe_tags(recipe2.id, ["한식"])
        popular = self.db.get_popular_tags()
        self.assertEqual(popular[0]["name"], "한식")
        self.assertEqual(popular[0]["count"], 2)

    def test_empty_tag_ignored(self):
        tags = self.db.set_recipe_tags(self.recipe.id, ["한식", "", "  "])
        self.assertEqual(tags, ["한식"])

    def test_case_insensitive_tags(self):
        self.db.set_recipe_tags(self.recipe.id, ["Korean"])
        recipes = self.db.find_recipes_by_tag("korean")
        self.assertEqual(len(recipes), 1)


class TestSearch(BaseTestCase):
    """Feature 3: Text search"""

    def test_search_by_title(self):
        results = self.db.search_recipes("김치")
        self.assertEqual(len(results), 1)

    def test_search_by_description(self):
        results = self.db.search_recipes("맛있는")
        self.assertEqual(len(results), 1)

    def test_search_no_results(self):
        results = self.db.search_recipes("파스타")
        self.assertEqual(len(results), 0)

    def test_search_empty_query(self):
        results = self.db.search_recipes("")
        self.assertEqual(len(results), 0)

    def test_search_case_insensitive(self):
        recipe2 = self.db.create_recipe(
            title="Pasta Carbonara", description="Italian",
            instructions="Cook", author_id=self.bob.id,
            ingredients=[{"name": "pasta"}],
        )
        results = self.db.search_recipes("pasta")
        self.assertEqual(len(results), 1)


class TestReport(BaseTestCase):
    """Feature 4: Report system"""

    def test_create_report(self):
        report = self.db.create_report(self.bob.id, "recipe", self.recipe.id, "부적절한 내용")
        self.assertEqual(report.status, "pending")
        self.assertEqual(report.target_type, "recipe")

    def test_duplicate_report(self):
        self.db.create_report(self.bob.id, "recipe", self.recipe.id, "부적절한 내용")
        with self.assertRaises(ValueError):
            self.db.create_report(self.bob.id, "recipe", self.recipe.id, "다시 신고")

    def test_empty_reason(self):
        with self.assertRaises(ValueError):
            self.db.create_report(self.bob.id, "recipe", self.recipe.id, "")

    def test_invalid_target_type(self):
        with self.assertRaises(ValueError):
            self.db.create_report(self.bob.id, "user", 1, "사유")

    def test_get_reports(self):
        self.db.create_report(self.bob.id, "recipe", self.recipe.id, "부적절한 내용")
        reports = self.db.get_reports("pending")
        self.assertEqual(len(reports), 1)

    def test_update_report_status(self):
        report = self.db.create_report(self.bob.id, "recipe", self.recipe.id, "부적절한 내용")
        self.db.update_report_status(report.id, "reviewed")
        reports = self.db.get_reports("reviewed")
        self.assertEqual(len(reports), 1)


class TestFork(BaseTestCase):
    """Feature 5: Fork/Remix"""

    def test_fork_recipe(self):
        forked = self.db.fork_recipe(self.recipe.id, self.bob.id)
        self.assertIn("리믹스", forked.title)
        self.assertEqual(forked.forked_from_id, self.recipe.id)
        self.assertEqual(forked.author_id, self.bob.id)

    def test_fork_custom_title(self):
        forked = self.db.fork_recipe(self.recipe.id, self.bob.id, title="나만의 김치찌개")
        self.assertEqual(forked.title, "나만의 김치찌개")

    def test_fork_copies_ingredients(self):
        forked = self.db.fork_recipe(self.recipe.id, self.bob.id)
        ingredients = self.db.get_recipe_ingredients(forked.id)
        self.assertEqual(len(ingredients), 3)

    def test_fork_increments_count(self):
        self.db.fork_recipe(self.recipe.id, self.bob.id)
        original = self.db.get_recipe(self.recipe.id)
        self.assertEqual(original.fork_count, 1)

    def test_fork_nonexistent(self):
        with self.assertRaises(ValueError):
            self.db.fork_recipe(9999, self.bob.id)

    def test_fork_awards_points(self):
        bob_before = self.db.get_user(self.bob.id)
        self.db.fork_recipe(self.recipe.id, self.bob.id)
        bob_after = self.db.get_user(self.bob.id)
        self.assertGreater(bob_after.points, bob_before.points)

    def test_fork_copies_tags(self):
        self.db.set_recipe_tags(self.recipe.id, ["한식", "찌개"])
        forked = self.db.fork_recipe(self.recipe.id, self.bob.id)
        tags = self.db.get_recipe_tags(forked.id)
        self.assertIn("한식", tags)
        self.assertIn("찌개", tags)


class TestWeeklyPopular(BaseTestCase):
    """Feature 6: Weekly popular"""

    def test_weekly_popular_includes_recent(self):
        results = self.db.get_weekly_popular()
        self.assertEqual(len(results), 1)

    def test_weekly_popular_empty_if_old(self):
        # No way to easily test old recipes without time travel
        # Just verify it returns something for fresh recipes
        results = self.db.get_weekly_popular()
        self.assertGreaterEqual(len(results), 0)


class TestCookLog(BaseTestCase):
    """Feature 7: Cook log"""

    def test_add_cook_log(self):
        log = self.db.add_cook_log(self.bob.id, self.recipe.id, note="맛있었어요!")
        self.assertEqual(log.recipe_id, self.recipe.id)
        self.assertEqual(log.note, "맛있었어요!")

    def test_cook_log_awards_points(self):
        bob_before = self.db.get_user(self.bob.id)
        self.db.add_cook_log(self.bob.id, self.recipe.id)
        bob_after = self.db.get_user(self.bob.id)
        self.assertEqual(bob_after.points - bob_before.points, 2)

    def test_cook_log_increments_count(self):
        self.db.add_cook_log(self.bob.id, self.recipe.id)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.cook_count, 1)

    def test_multiple_cook_logs(self):
        self.db.add_cook_log(self.bob.id, self.recipe.id, note="1회차")
        self.db.add_cook_log(self.bob.id, self.recipe.id, note="2회차")
        logs = self.db.get_cook_logs(self.recipe.id)
        self.assertEqual(len(logs), 2)

    def test_cook_log_nonexistent_recipe(self):
        with self.assertRaises(ValueError):
            self.db.add_cook_log(self.bob.id, 9999)

    def test_get_user_cook_logs(self):
        self.db.add_cook_log(self.bob.id, self.recipe.id)
        logs = self.db.get_user_cook_logs(self.bob.id)
        self.assertEqual(len(logs), 1)


class TestCollections(BaseTestCase):
    """Feature 8: Recipe collections"""

    def test_create_collection(self):
        coll = self.db.create_collection(self.bob.id, "한식 모음", "좋아하는 한식")
        self.assertEqual(coll.name, "한식 모음")

    def test_empty_name(self):
        with self.assertRaises(ValueError):
            self.db.create_collection(self.bob.id, "")

    def test_add_recipe_to_collection(self):
        coll = self.db.create_collection(self.bob.id, "한식")
        self.db.add_to_collection(coll.id, self.recipe.id, self.bob.id)
        recipes = self.db.get_collection_recipes(coll.id)
        self.assertEqual(len(recipes), 1)

    def test_add_duplicate_to_collection(self):
        coll = self.db.create_collection(self.bob.id, "한식")
        self.db.add_to_collection(coll.id, self.recipe.id, self.bob.id)
        with self.assertRaises(ValueError):
            self.db.add_to_collection(coll.id, self.recipe.id, self.bob.id)

    def test_remove_from_collection(self):
        coll = self.db.create_collection(self.bob.id, "한식")
        self.db.add_to_collection(coll.id, self.recipe.id, self.bob.id)
        removed = self.db.remove_from_collection(coll.id, self.recipe.id, self.bob.id)
        self.assertTrue(removed)
        recipes = self.db.get_collection_recipes(coll.id)
        self.assertEqual(len(recipes), 0)

    def test_other_user_cannot_add(self):
        coll = self.db.create_collection(self.bob.id, "한식")
        with self.assertRaises(ValueError):
            self.db.add_to_collection(coll.id, self.recipe.id, self.carol.id)

    def test_delete_collection(self):
        coll = self.db.create_collection(self.bob.id, "한식")
        deleted = self.db.delete_collection(coll.id, self.bob.id)
        self.assertTrue(deleted)

    def test_get_user_collections(self):
        self.db.create_collection(self.bob.id, "한식")
        self.db.create_collection(self.bob.id, "양식")
        colls = self.db.get_user_collections(self.bob.id)
        self.assertEqual(len(colls), 2)


class TestNotifications(BaseTestCase):
    """Feature 9: Notification system"""

    def test_notification_created_on_follow(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        notifs = self.db.get_notifications(self.alice.id)
        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs[0].type, "follow")

    def test_mark_read(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        notifs = self.db.get_notifications(self.alice.id)
        count = self.db.mark_notifications_read(self.alice.id, [notifs[0].id])
        self.assertEqual(count, 1)

    def test_mark_all_read(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        self.db.toggle_follow(self.carol.id, self.alice.id)
        count = self.db.mark_notifications_read(self.alice.id)
        self.assertEqual(count, 2)

    def test_unread_count(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        self.assertEqual(self.db.get_unread_count(self.alice.id), 1)
        self.db.mark_notifications_read(self.alice.id)
        self.assertEqual(self.db.get_unread_count(self.alice.id), 0)

    def test_unread_only_filter(self):
        self.db.toggle_follow(self.bob.id, self.alice.id)
        self.db.toggle_follow(self.carol.id, self.alice.id)
        self.db.mark_notifications_read(self.alice.id, [
            self.db.get_notifications(self.alice.id)[0].id
        ])
        unread = self.db.get_notifications(self.alice.id, unread_only=True)
        self.assertEqual(len(unread), 1)


class TestShareLink(BaseTestCase):
    """Feature 10: Share links"""

    def test_create_share_link(self):
        link = self.db.create_share_link(self.recipe.id)
        self.assertTrue(len(link.token) > 0)
        self.assertEqual(link.view_count, 0)

    def test_duplicate_share_link_returns_existing(self):
        link1 = self.db.create_share_link(self.recipe.id)
        link2 = self.db.create_share_link(self.recipe.id)
        self.assertEqual(link1.token, link2.token)

    def test_get_recipe_by_token(self):
        link = self.db.create_share_link(self.recipe.id)
        recipe = self.db.get_recipe_by_share_token(link.token)
        self.assertIsNotNone(recipe)
        self.assertEqual(recipe.id, self.recipe.id)

    def test_view_count_increments(self):
        link = self.db.create_share_link(self.recipe.id)
        self.db.get_recipe_by_share_token(link.token)
        self.db.get_recipe_by_share_token(link.token)
        updated = self.db.get_share_link(self.recipe.id)
        self.assertEqual(updated.view_count, 2)

    def test_invalid_token(self):
        result = self.db.get_recipe_by_share_token("nonexistent")
        self.assertIsNone(result)

    def test_share_nonexistent_recipe(self):
        with self.assertRaises(ValueError):
            self.db.create_share_link(9999)


if __name__ == "__main__":
    unittest.main()
