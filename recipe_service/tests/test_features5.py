"""Tests for features 71-120."""

import json
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


class TestRatingReviews(BaseTestCase):
    """Feature 71"""
    def test_add_and_get(self):
        review = self.db.add_rating_review(0, self.bob.id, self.recipe.id, "맛있어요")
        self.assertEqual(review.text, "맛있어요")
        reviews = self.db.get_rating_reviews(self.recipe.id)
        self.assertEqual(len(reviews), 1)


class TestIngredientGroups(BaseTestCase):
    """Feature 72"""
    def test_set_and_get(self):
        self.db.set_ingredient_groups(self.recipe.id, [{"group_name": "양념"}, {"group_name": "주재료"}])
        groups = self.db.get_ingredient_groups(self.recipe.id)
        self.assertEqual(len(groups), 2)

    def test_replace(self):
        self.db.set_ingredient_groups(self.recipe.id, [{"group_name": "양념"}])
        self.db.set_ingredient_groups(self.recipe.id, [{"group_name": "소스"}])
        groups = self.db.get_ingredient_groups(self.recipe.id)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["group_name"], "소스")


class TestRecipeDrafts(BaseTestCase):
    """Feature 73"""
    def test_save_and_get(self):
        draft = self.db.save_draft(self.alice.id, "테스트", '{"title":"test"}')
        self.assertEqual(draft.title, "테스트")
        drafts = self.db.get_drafts(self.alice.id)
        self.assertEqual(len(drafts), 1)

    def test_delete(self):
        draft = self.db.save_draft(self.alice.id, "테스트", '{}')
        self.assertTrue(self.db.delete_draft(draft.id, self.alice.id))
        self.assertEqual(len(self.db.get_drafts(self.alice.id)), 0)


class TestCookingProgress(BaseTestCase):
    """Feature 74"""
    def test_update_and_get(self):
        p = self.db.update_cooking_progress(self.bob.id, self.recipe.id, 2, 5)
        self.assertEqual(p.current_step, 2)
        got = self.db.get_cooking_progress(self.bob.id, self.recipe.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.total_steps, 5)

    def test_clear(self):
        self.db.update_cooking_progress(self.bob.id, self.recipe.id, 1, 3)
        self.assertTrue(self.db.clear_cooking_progress(self.bob.id, self.recipe.id))
        self.assertIsNone(self.db.get_cooking_progress(self.bob.id, self.recipe.id))


class TestRecipeSource(BaseTestCase):
    """Feature 75"""
    def test_set_and_get(self):
        src = self.db.set_recipe_source(self.recipe.id, "https://example.com", "Example")
        self.assertEqual(src.url, "https://example.com")
        got = self.db.get_recipe_source(self.recipe.id)
        self.assertIsNotNone(got)

    def test_no_source(self):
        self.assertIsNone(self.db.get_recipe_source(self.recipe.id))


class TestMenuSuggestion(BaseTestCase):
    """Feature 76"""
    def test_suggestions(self):
        recipes = self.db.get_menu_suggestions("lunch", limit=5)
        self.assertIsInstance(recipes, list)


class TestCostLog(BaseTestCase):
    """Feature 77"""
    def test_log_and_get(self):
        log = self.db.log_cooking_cost(self.bob.id, self.recipe.id, 15000, "재료비")
        self.assertEqual(log.amount, 15000)
        logs = self.db.get_cost_logs(self.bob.id)
        self.assertEqual(len(logs), 1)

    def test_total(self):
        self.db.log_cooking_cost(self.bob.id, self.recipe.id, 10000)
        self.db.log_cooking_cost(self.bob.id, self.recipe.id, 5000)
        total = self.db.get_total_cost(self.bob.id, days=30)
        self.assertAlmostEqual(total, 15000)


class TestReactions(BaseTestCase):
    """Feature 78"""
    def test_add_and_get(self):
        self.db.add_reaction(self.bob.id, self.recipe.id, "👍")
        reactions = self.db.get_reactions(self.recipe.id)
        self.assertEqual(len(reactions), 1)
        self.assertEqual(reactions[0]["emoji"], "👍")

    def test_remove(self):
        self.db.add_reaction(self.bob.id, self.recipe.id, "👍")
        self.assertTrue(self.db.remove_reaction(self.bob.id, self.recipe.id, "👍"))
        self.assertEqual(len(self.db.get_reactions(self.recipe.id)), 0)

    def test_duplicate(self):
        self.db.add_reaction(self.bob.id, self.recipe.id, "👍")
        with self.assertRaises(ValueError):
            self.db.add_reaction(self.bob.id, self.recipe.id, "👍")


class TestPlaylist(BaseTestCase):
    """Feature 79"""
    def test_create_and_add(self):
        pl = self.db.create_playlist(self.alice.id, "주말 요리")
        self.db.add_to_playlist(pl.id, self.recipe.id)
        recipes = self.db.get_playlist_recipes(pl.id)
        self.assertEqual(len(recipes), 1)

    def test_user_playlists(self):
        self.db.create_playlist(self.alice.id, "리스트1")
        self.db.create_playlist(self.alice.id, "리스트2")
        pls = self.db.get_user_playlists(self.alice.id)
        self.assertEqual(len(pls), 2)

    def test_delete(self):
        pl = self.db.create_playlist(self.alice.id, "삭제용")
        self.assertTrue(self.db.delete_playlist(pl.id, self.alice.id))


class TestCertification(BaseTestCase):
    """Feature 80"""
    def test_certify(self):
        self.db.certify_recipe(self.recipe.id, self.alice.id)
        self.assertTrue(self.db.is_certified(self.recipe.id))

    def test_not_certified(self):
        self.assertFalse(self.db.is_certified(self.recipe.id))

    def test_certified_list(self):
        self.db.certify_recipe(self.recipe.id, self.alice.id)
        recipes = self.db.get_certified_recipes()
        self.assertEqual(len(recipes), 1)


class TestIngredientSeason(BaseTestCase):
    """Feature 81"""
    def test_set_and_get(self):
        self.db.set_ingredient_season("딸기", ["spring", "winter"])
        ings = self.db.get_seasonal_ingredients("spring")
        self.assertIn("딸기", ings)


class TestTimerPresets(BaseTestCase):
    """Feature 82"""
    def test_save_and_get(self):
        self.db.save_timer_preset(self.alice.id, "파스타", '[{"label":"끓이기","seconds":600}]')
        presets = self.db.get_timer_presets(self.alice.id)
        self.assertEqual(len(presets), 1)

    def test_delete(self):
        p = self.db.save_timer_preset(self.alice.id, "삭제용", '[]')
        self.assertTrue(self.db.delete_timer_preset(p.id, self.alice.id))


class TestEditHistory(BaseTestCase):
    """Feature 83"""
    def test_log_and_get(self):
        self.db.log_recipe_edit(self.recipe.id, self.alice.id, "title", "old", "new")
        history = self.db.get_edit_history(self.recipe.id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].field_name, "title")


class TestSocialShares(BaseTestCase):
    """Feature 84"""
    def test_track_and_get(self):
        self.db.track_social_share(self.recipe.id, "twitter")
        self.db.track_social_share(self.recipe.id, "twitter")
        shares = self.db.get_social_shares(self.recipe.id)
        self.assertEqual(shares[0]["count"], 2)


class TestTemplates(BaseTestCase):
    """Feature 85"""
    def test_create_and_list(self):
        t = self.db.create_template("기본", "기본 템플릿", '{"servings":2}')
        self.assertEqual(t.name, "기본")
        templates = self.db.get_templates()
        self.assertEqual(len(templates), 1)

    def test_duplicate(self):
        self.db.create_template("기본", "", '{}')
        with self.assertRaises(ValueError):
            self.db.create_template("기본", "", '{}')


class TestCookingSkill(BaseTestCase):
    """Feature 86"""
    def test_set_and_get(self):
        self.db.set_cooking_skill(self.alice.id, "advanced")
        self.assertEqual(self.db.get_cooking_skill(self.alice.id), "advanced")

    def test_default(self):
        self.assertEqual(self.db.get_cooking_skill(self.alice.id), "beginner")

    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.db.set_cooking_skill(self.alice.id, "master")


class TestDefaultServings(BaseTestCase):
    """Feature 87"""
    def test_set_and_get(self):
        self.db.set_default_servings(self.alice.id, 4)
        self.assertEqual(self.db.get_default_servings(self.alice.id), 4)

    def test_default(self):
        self.assertEqual(self.db.get_default_servings(self.alice.id), 2)


class TestArchive(BaseTestCase):
    """Feature 88"""
    def test_archive_and_list(self):
        self.assertTrue(self.db.archive_recipe(self.recipe.id, self.alice.id))
        archived = self.db.get_archived_recipes(self.alice.id)
        self.assertEqual(len(archived), 1)

    def test_unarchive(self):
        self.db.archive_recipe(self.recipe.id, self.alice.id)
        self.assertTrue(self.db.unarchive_recipe(self.recipe.id, self.alice.id))
        self.assertEqual(len(self.db.get_archived_recipes(self.alice.id)), 0)


class TestIngredientStats(BaseTestCase):
    """Feature 89"""
    def test_global_stats(self):
        stats = self.db.get_ingredient_usage_stats()
        self.assertGreater(len(stats), 0)

    def test_user_stats(self):
        stats = self.db.get_user_ingredient_stats(self.alice.id)
        self.assertGreater(len(stats), 0)


class TestAutoMenu(BaseTestCase):
    """Feature 90"""
    def test_generate(self):
        r2 = self.db.create_recipe(title="비빔밥", description="", instructions="섞는다",
                                    author_id=self.alice.id, ingredients=[{"name": "밥"}])
        result = self.db.generate_weekly_menu(self.bob.id, "2026-05-01")
        self.assertIsInstance(result, list)


class TestCostCompare(BaseTestCase):
    """Feature 91"""
    def test_compare(self):
        r2 = self.db.create_recipe(title="비빔밥", description="", instructions="섞는다",
                                    author_id=self.alice.id, ingredients=[{"name": "밥"}])
        result = self.db.compare_recipe_costs([self.recipe.id, r2.id])
        self.assertEqual(len(result), 2)


class TestAchievementsV2(BaseTestCase):
    """Feature 92"""
    def test_create_and_check(self):
        self.db.create_achievement("chef_1", "셰프1", "레시피 1개", "recipes_created", 1)
        awarded = self.db.check_achievements(self.alice.id)
        self.assertIn("chef_1", awarded)

    def test_get_achievements(self):
        self.db.create_achievement("chef_1", "셰프1", "", "recipes_created", 1)
        self.db.check_achievements(self.alice.id)
        achs = self.db.get_user_achievements(self.alice.id)
        self.assertEqual(len(achs), 1)


class TestHashtags(BaseTestCase):
    """Feature 93"""
    def test_add_and_search(self):
        self.db.add_hashtag(self.recipe.id, "#매운맛")
        recipes = self.db.search_by_hashtag("매운맛")
        self.assertEqual(len(recipes), 1)

    def test_trending(self):
        self.db.add_hashtag(self.recipe.id, "한식")
        tags = self.db.get_trending_hashtags()
        self.assertGreater(len(tags), 0)

    def test_remove(self):
        self.db.add_hashtag(self.recipe.id, "test")
        self.assertTrue(self.db.remove_hashtag(self.recipe.id, "test"))


class TestPriceAlerts(BaseTestCase):
    """Feature 94"""
    def test_set_and_get(self):
        alert = self.db.set_price_alert(self.alice.id, "김치", 5000)
        self.assertEqual(alert.max_price, 5000)
        alerts = self.db.get_price_alerts(self.alice.id)
        self.assertEqual(len(alerts), 1)

    def test_check(self):
        self.db.set_price_alert(self.alice.id, "김치", 5000)
        self.db.set_ingredient_price("김치", 3000)
        triggered = self.db.check_price_alerts(self.alice.id)
        self.assertEqual(len(triggered), 1)


class TestCollaboration(BaseTestCase):
    """Feature 95"""
    def test_invite_and_list(self):
        self.db.invite_collaborator(self.recipe.id, self.bob.id)
        collabs = self.db.get_collaborators(self.recipe.id)
        self.assertEqual(len(collabs), 1)

    def test_remove(self):
        self.db.invite_collaborator(self.recipe.id, self.bob.id)
        self.assertTrue(self.db.remove_collaborator(self.recipe.id, self.bob.id))

    def test_duplicate(self):
        self.db.invite_collaborator(self.recipe.id, self.bob.id)
        with self.assertRaises(ValueError):
            self.db.invite_collaborator(self.recipe.id, self.bob.id)


class TestCookingClass(BaseTestCase):
    """Feature 96"""
    def test_create_and_join(self):
        c = self.db.create_cooking_class("파스타 교실", "초보용", self.alice.id, "2026-06-01", 10)
        result = self.db.join_cooking_class(c.id, self.bob.id)
        self.assertEqual(result["participants"], 1)

    def test_list(self):
        self.db.create_cooking_class("교실1", "", self.alice.id, "2030-01-01")
        classes = self.db.get_cooking_classes()
        self.assertGreaterEqual(len(classes), 1)

    def test_full_class(self):
        c = self.db.create_cooking_class("소규모", "", self.alice.id, "2030-01-01", 1)
        self.db.join_cooking_class(c.id, self.bob.id)
        charlie = self.db.create_user("charlie", "c@test.com", "pass1234")
        with self.assertRaises(ValueError):
            self.db.join_cooking_class(c.id, charlie.id)


class TestBundles(BaseTestCase):
    """Feature 97"""
    def test_create_and_add(self):
        b = self.db.create_bundle(self.alice.id, "한식 모음")
        self.db.add_to_bundle(b.id, self.recipe.id)
        recipes = self.db.get_bundle_recipes(b.id)
        self.assertEqual(len(recipes), 1)

    def test_list(self):
        self.db.create_bundle(self.alice.id, "번들1")
        bundles = self.db.get_bundles()
        self.assertEqual(len(bundles), 1)


class TestMealPrep(BaseTestCase):
    """Feature 98"""
    def test_create_and_add(self):
        mp = self.db.create_meal_prep(self.alice.id, "주말 밀프렙", "2026-04-05", 6)
        self.db.add_meal_prep_recipe(mp.id, self.recipe.id)
        recipes = self.db.get_meal_prep_recipes(mp.id)
        self.assertEqual(len(recipes), 1)

    def test_user_preps(self):
        self.db.create_meal_prep(self.alice.id, "프렙1", "2026-04-05")
        preps = self.db.get_user_meal_preps(self.alice.id)
        self.assertEqual(len(preps), 1)


class TestRecipeAnalytics(BaseTestCase):
    """Feature 99"""
    def test_recipe_analytics(self):
        analytics = self.db.get_recipe_analytics(self.recipe.id)
        self.assertEqual(analytics["recipe_id"], self.recipe.id)
        self.assertIn("views", analytics)

    def test_author_analytics(self):
        analytics = self.db.get_author_analytics(self.alice.id)
        self.assertEqual(analytics["total_recipes"], 1)


class TestFlavorProfile(BaseTestCase):
    """Feature 100"""
    def test_set_and_get(self):
        self.db.set_flavor_profile(self.recipe.id, sweet=1, salty=3, spicy=5)
        f = self.db.get_flavor_profile(self.recipe.id)
        self.assertEqual(f["spicy"], 5)
        self.assertEqual(f["salty"], 3)

    def test_find_by_flavor(self):
        self.db.set_flavor_profile(self.recipe.id, spicy=5)
        recipes = self.db.find_by_flavor("spicy", min_score=3)
        self.assertEqual(len(recipes), 1)

    def test_no_profile(self):
        self.assertIsNone(self.db.get_flavor_profile(self.recipe.id))


class TestApprovalQueue(BaseTestCase):
    """Feature 101"""
    def test_submit_and_approve(self):
        self.db.submit_for_approval(self.recipe.id, self.alice.id)
        pending = self.db.get_pending_approvals()
        self.assertEqual(len(pending), 1)
        result = self.db.approve_recipe_submission(self.recipe.id, self.bob.id)
        self.assertTrue(result["updated"])

    def test_reject(self):
        self.db.submit_for_approval(self.recipe.id, self.alice.id)
        result = self.db.reject_recipe_submission(self.recipe.id, self.bob.id, "품질 미달")
        self.assertTrue(result["updated"])

    def test_duplicate_submit(self):
        self.db.submit_for_approval(self.recipe.id, self.alice.id)
        with self.assertRaises(ValueError):
            self.db.submit_for_approval(self.recipe.id, self.alice.id)


class TestJournal(BaseTestCase):
    """Feature 102"""
    def test_add_and_get(self):
        entry = self.db.add_journal_entry(self.alice.id, "2026-04-01", "오늘 김치찌개 만듦", mood="happy")
        self.assertEqual(entry.mood, "happy")
        entries = self.db.get_journal_entries(self.alice.id)
        self.assertEqual(len(entries), 1)

    def test_date_filter(self):
        self.db.add_journal_entry(self.alice.id, "2026-04-01", "일지1")
        self.db.add_journal_entry(self.alice.id, "2026-04-10", "일지2")
        entries = self.db.get_journal_entries(self.alice.id, start_date="2026-04-05")
        self.assertEqual(len(entries), 1)


class TestRemixChain(BaseTestCase):
    """Feature 103"""
    def test_chain(self):
        chain = self.db.get_remix_chain(self.recipe.id)
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0]["id"], self.recipe.id)

    def test_tree(self):
        forked = self.db.fork_recipe(self.recipe.id, self.bob.id)
        tree = self.db.get_remix_tree(self.recipe.id)
        self.assertEqual(len(tree), 1)


class TestIngredientPairing(BaseTestCase):
    """Feature 104"""
    def test_add_and_get(self):
        self.db.add_ingredient_pairing("김치", "돼지고기", 9)
        pairs = self.db.get_pairings("김치")
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["score"], 9)

    def test_suggest(self):
        self.db.add_ingredient_pairing("김치", "참치", 8)
        suggestions = self.db.suggest_pairings(self.recipe.id)
        self.assertIsInstance(suggestions, list)


class TestMoodTags(BaseTestCase):
    """Feature 105"""
    def test_set_and_get(self):
        self.db.set_mood_tags(self.recipe.id, ["comfort", "warm"])
        moods = self.db.get_mood_tags(self.recipe.id)
        self.assertEqual(len(moods), 2)

    def test_find_by_mood(self):
        self.db.set_mood_tags(self.recipe.id, ["comfort"])
        recipes = self.db.find_by_mood("comfort")
        self.assertEqual(len(recipes), 1)


class TestSpeedChallenge(BaseTestCase):
    """Feature 106"""
    def test_create_and_submit(self):
        ch = self.db.create_speed_challenge(self.recipe.id, 30)
        self.db.submit_speed_result(ch["id"], self.bob.id, 25)
        rankings = self.db.get_speed_rankings(ch["id"])
        self.assertEqual(len(rankings), 1)
        self.assertEqual(rankings[0]["actual_minutes"], 25)


class TestRecipeGift(BaseTestCase):
    """Feature 107"""
    def test_send_and_receive(self):
        gift = self.db.send_recipe_gift(self.alice.id, self.bob.id, self.recipe.id, "맛있게 드세요!")
        received = self.db.get_received_gifts(self.bob.id)
        self.assertEqual(len(received), 1)
        sent = self.db.get_sent_gifts(self.alice.id)
        self.assertEqual(len(sent), 1)

    def test_open(self):
        gift = self.db.send_recipe_gift(self.alice.id, self.bob.id, self.recipe.id)
        self.assertTrue(self.db.open_gift(gift["id"], self.bob.id))


class TestIngredientWiki(BaseTestCase):
    """Feature 108"""
    def test_add_and_get(self):
        self.db.add_ingredient_info("김치", description="한국의 발효식품", tips="잘 익은 것 사용", storage="냉장보관")
        info = self.db.get_ingredient_info("김치")
        self.assertIsNotNone(info)
        self.assertIn("발효", info["description"])

    def test_search(self):
        self.db.add_ingredient_info("김치", description="발효식품")
        results = self.db.search_ingredient_wiki("발효")
        self.assertGreater(len(results), 0)


class TestRecipeCalendar(BaseTestCase):
    """Feature 109"""
    def test_calendar(self):
        self.db.set_meal_plan(self.alice.id, "2026-04-15", "lunch", self.recipe.id)
        cal = self.db.get_recipe_calendar(self.alice.id, 2026, 4)
        self.assertIn("2026-04-15", cal["days"])


class TestCookingTechnique(BaseTestCase):
    """Feature 110"""
    def test_add_and_link(self):
        t = self.db.add_technique("볶기", "팬에 볶는 기법", "easy")
        self.db.link_technique_to_recipe(self.recipe.id, t["id"])
        techs = self.db.get_recipe_techniques(self.recipe.id)
        self.assertEqual(len(techs), 1)

    def test_list(self):
        self.db.add_technique("굽기")
        techs = self.db.get_techniques()
        self.assertGreater(len(techs), 0)


class TestChefEndorsement(BaseTestCase):
    """Feature 111"""
    def test_endorse(self):
        self.db.endorse_recipe(self.bob.id, self.recipe.id, "훌륭합니다")
        endorsements = self.db.get_endorsements(self.recipe.id)
        self.assertEqual(len(endorsements), 1)

    def test_duplicate(self):
        self.db.endorse_recipe(self.bob.id, self.recipe.id)
        with self.assertRaises(ValueError):
            self.db.endorse_recipe(self.bob.id, self.recipe.id)

    def test_endorsed_list(self):
        self.db.endorse_recipe(self.bob.id, self.recipe.id)
        recipes = self.db.get_endorsed_recipes()
        self.assertEqual(len(recipes), 1)


class TestIngredientOrigin(BaseTestCase):
    """Feature 112"""
    def test_set_and_get(self):
        self.db.set_ingredient_origin("김치", "한국", "전통 발효식품")
        origin = self.db.get_ingredient_origin("김치")
        self.assertIsNotNone(origin)
        self.assertEqual(origin["origin"], "한국")

    def test_not_found(self):
        self.assertIsNone(self.db.get_ingredient_origin("unknown"))


class TestEventRecipe(BaseTestCase):
    """Feature 113"""
    def test_create_and_link(self):
        ev = self.db.create_event("추석", "2026-09-25", "추석 요리")
        self.db.link_recipe_to_event(ev["id"], self.recipe.id)
        recipes = self.db.get_event_recipes(ev["id"])
        self.assertEqual(len(recipes), 1)


class TestGroupCook(BaseTestCase):
    """Feature 114"""
    def test_create_and_join(self):
        gc = self.db.create_group_cook(self.recipe.id, self.alice.id, "2030-01-01", 5)
        result = self.db.join_group_cook(gc["id"], self.bob.id)
        self.assertEqual(result["members"], 1)
        members = self.db.get_group_members(gc["id"])
        self.assertEqual(len(members), 1)


class TestNutritionMatch(BaseTestCase):
    """Feature 115"""
    def test_match(self):
        self.db.set_nutrition(self.recipe.id, calories=500, protein_g=25)
        recipes = self.db.find_nutrition_matching(target_calories=500, tolerance=0.2)
        self.assertGreaterEqual(len(recipes), 1)


class TestStores(BaseTestCase):
    """Feature 116"""
    def test_add_and_find(self):
        store = self.db.add_store("동네마트", "서울시", "로컬 마트")
        self.db.link_ingredient_to_store(store["id"], "김치", 3000)
        stores = self.db.find_stores_for_ingredient("김치")
        self.assertEqual(len(stores), 1)


class TestRecipeStory(BaseTestCase):
    """Feature 117"""
    def test_set_and_get(self):
        self.db.set_recipe_story(self.recipe.id, "어머니의 레시피입니다")
        story = self.db.get_recipe_story(self.recipe.id)
        self.assertEqual(story, "어머니의 레시피입니다")

    def test_no_story(self):
        self.assertIsNone(self.db.get_recipe_story(self.recipe.id))


class TestCookingFaq(BaseTestCase):
    """Feature 118"""
    def test_add_and_get(self):
        self.db.add_faq("소금은 언제 넣나요?", "끓기 시작할 때", "seasoning")
        faqs = self.db.get_faqs("seasoning")
        self.assertEqual(len(faqs), 1)

    def test_search(self):
        self.db.add_faq("소금은 언제?", "끓을 때")
        results = self.db.search_faqs("소금")
        self.assertGreater(len(results), 0)


class TestRecipeRankings(BaseTestCase):
    """Feature 119"""
    def test_rankings(self):
        rankings = self.db.get_recipe_rankings(limit=10)
        self.assertIsInstance(rankings, list)


class TestWeeklyDigest(BaseTestCase):
    """Feature 120"""
    def test_digest(self):
        digest = self.db.generate_weekly_digest(self.bob.id)
        self.assertIn("new_from_following", digest)
        self.assertIn("popular_this_week", digest)
        self.assertIn("new_followers", digest)


if __name__ == "__main__":
    unittest.main()
