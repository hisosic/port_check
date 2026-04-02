"""Tests for the bookmark (즐겨찾기) feature."""

import os
import tempfile
import time
import unittest

from recipe_service.models import Database, Bookmark


class TestBookmarks(unittest.TestCase):
    """Test bookmark toggle, status, and listing."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        # Create two users and a recipe
        self.user1 = self.db.create_user("alice", "alice@test.com", "pass1234")
        self.user2 = self.db.create_user("bob", "bob@test.com", "pass1234")
        self.recipe = self.db.create_recipe(
            title="김치찌개",
            description="맛있는 김치찌개",
            instructions="끓인다",
            author_id=self.user1.id,
            ingredients=[{"name": "김치"}, {"name": "돼지고기"}],
        )

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_bookmark_toggle_on(self):
        result = self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        self.assertTrue(result["bookmarked"])
        self.assertEqual(result["bookmark_count"], 1)

    def test_bookmark_toggle_off(self):
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        result = self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        self.assertFalse(result["bookmarked"])
        self.assertEqual(result["bookmark_count"], 0)

    def test_bookmark_toggle_on_again(self):
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        result = self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        self.assertTrue(result["bookmarked"])
        self.assertEqual(result["bookmark_count"], 1)

    def test_is_bookmarked(self):
        self.assertFalse(self.db.is_bookmarked(self.user2.id, self.recipe.id))
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        self.assertTrue(self.db.is_bookmarked(self.user2.id, self.recipe.id))

    def test_bookmark_nonexistent_recipe(self):
        with self.assertRaises(ValueError):
            self.db.toggle_bookmark(self.user2.id, 9999)

    def test_get_user_bookmarks_empty(self):
        bookmarks = self.db.get_user_bookmarks(self.user2.id)
        self.assertEqual(len(bookmarks), 0)

    def test_get_user_bookmarks(self):
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        bookmarks = self.db.get_user_bookmarks(self.user2.id)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].id, self.recipe.id)
        self.assertEqual(bookmarks[0].title, "김치찌개")

    def test_bookmark_own_recipe(self):
        """Authors can bookmark their own recipes."""
        result = self.db.toggle_bookmark(self.user1.id, self.recipe.id)
        self.assertTrue(result["bookmarked"])
        self.assertEqual(result["bookmark_count"], 1)

    def test_multiple_users_bookmark(self):
        self.db.toggle_bookmark(self.user1.id, self.recipe.id)
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.bookmark_count, 2)

    def test_bookmark_count_in_recipe(self):
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.bookmark_count, 1)
        # Unbookmark
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        recipe = self.db.get_recipe(self.recipe.id)
        self.assertEqual(recipe.bookmark_count, 0)

    def test_get_user_bookmarks_order(self):
        """Bookmarks should be ordered by newest first."""
        recipe2 = self.db.create_recipe(
            title="된장찌개",
            description="맛있는 된장찌개",
            instructions="끓인다",
            author_id=self.user1.id,
            ingredients=[{"name": "된장"}, {"name": "두부"}],
        )
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        time.sleep(0.05)
        self.db.toggle_bookmark(self.user2.id, recipe2.id)
        bookmarks = self.db.get_user_bookmarks(self.user2.id)
        self.assertEqual(len(bookmarks), 2)
        # Most recent bookmark first
        self.assertEqual(bookmarks[0].id, recipe2.id)
        self.assertEqual(bookmarks[1].id, self.recipe.id)

    def test_unbookmark_preserves_others(self):
        """Unbookmarking one recipe doesn't affect other bookmarks."""
        recipe2 = self.db.create_recipe(
            title="된장찌개",
            description="맛있는 된장찌개",
            instructions="끓인다",
            author_id=self.user1.id,
            ingredients=[{"name": "된장"}],
        )
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        self.db.toggle_bookmark(self.user2.id, recipe2.id)
        # Unbookmark first recipe
        self.db.toggle_bookmark(self.user2.id, self.recipe.id)
        bookmarks = self.db.get_user_bookmarks(self.user2.id)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].id, recipe2.id)


if __name__ == "__main__":
    unittest.main()
