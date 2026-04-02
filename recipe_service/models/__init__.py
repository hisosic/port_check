"""Database models for FridgeChef recipe service."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent / "fridgechef.db"


@dataclass
class User:
    id: int = 0
    username: str = ""
    email: str = ""
    password_hash: str = ""
    points: int = 0
    created_at: float = 0.0
    is_active: bool = True


@dataclass
class Recipe:
    id: int = 0
    title: str = ""
    description: str = ""
    instructions: str = ""
    author_id: int = 0
    cooking_time_min: int = 0
    servings: int = 1
    difficulty: str = "easy"  # easy, medium, hard
    like_count: int = 0
    comment_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    bookmark_count: int = 0
    fork_count: int = 0
    cook_count: int = 0
    view_count: int = 0
    season: str = ""  # spring, summer, fall, winter, all
    category: str = ""  # korean, chinese, japanese, western, etc.
    is_public: bool = True
    scheduled_at: float | None = None
    forked_from_id: int | None = None
    created_at: float = 0.0
    author_name: str = ""  # joined field


@dataclass
class Rating:
    id: int = 0
    recipe_id: int = 0
    user_id: int = 0
    score: int = 0  # 1~5
    created_at: float = 0.0
    username: str = ""  # joined field


@dataclass
class Ingredient:
    id: int = 0
    recipe_id: int = 0
    name: str = ""
    amount: str = ""
    unit: str = ""


@dataclass
class Like:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    created_at: float = 0.0


@dataclass
class PointHistory:
    id: int = 0
    user_id: int = 0
    amount: int = 0
    reason: str = ""
    created_at: float = 0.0


@dataclass
class Bookmark:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    created_at: float = 0.0


@dataclass
class Comment:
    id: int = 0
    recipe_id: int = 0
    user_id: int = 0
    content: str = ""
    parent_id: int | None = None
    created_at: float = 0.0
    updated_at: float = 0.0
    username: str = ""  # joined field


@dataclass
class Follow:
    id: int = 0
    follower_id: int = 0
    following_id: int = 0
    created_at: float = 0.0


@dataclass
class Tag:
    id: int = 0
    name: str = ""


@dataclass
class RecipeTag:
    id: int = 0
    recipe_id: int = 0
    tag_id: int = 0


@dataclass
class Report:
    id: int = 0
    reporter_id: int = 0
    target_type: str = ""  # "recipe" or "comment"
    target_id: int = 0
    reason: str = ""
    status: str = "pending"  # pending, reviewed, dismissed
    created_at: float = 0.0


@dataclass
class CookLog:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    note: str = ""
    photo_url: str = ""
    created_at: float = 0.0
    username: str = ""  # joined field


@dataclass
class Collection:
    id: int = 0
    user_id: int = 0
    name: str = ""
    description: str = ""
    created_at: float = 0.0


@dataclass
class CollectionItem:
    id: int = 0
    collection_id: int = 0
    recipe_id: int = 0
    added_at: float = 0.0


@dataclass
class Notification:
    id: int = 0
    user_id: int = 0
    type: str = ""  # like, comment, follow, rating
    message: str = ""
    reference_id: int = 0
    is_read: bool = False
    created_at: float = 0.0


@dataclass
class ShareLink:
    id: int = 0
    recipe_id: int = 0
    token: str = ""
    view_count: int = 0
    created_at: float = 0.0


@dataclass
class Reply:
    id: int = 0
    comment_id: int = 0
    user_id: int = 0
    content: str = ""
    created_at: float = 0.0
    username: str = ""  # joined field


@dataclass
class UserProfile:
    user_id: int = 0
    bio: str = ""
    avatar_url: str = ""
    website: str = ""
    updated_at: float = 0.0


@dataclass
class RecipeImage:
    id: int = 0
    recipe_id: int = 0
    image_url: str = ""
    caption: str = ""
    sort_order: int = 0
    created_at: float = 0.0


@dataclass
class NutritionInfo:
    id: int = 0
    recipe_id: int = 0
    calories: int = 0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0


@dataclass
class RecipeStep:
    id: int = 0
    recipe_id: int = 0
    step_number: int = 0
    title: str = ""
    description: str = ""
    image_url: str = ""
    timer_minutes: int = 0


@dataclass
class IngredientPrice:
    id: int = 0
    name: str = ""
    price: float = 0.0
    unit: str = ""
    updated_at: float = 0.0


@dataclass
class Badge:
    id: int = 0
    code: str = ""
    name: str = ""
    description: str = ""
    icon: str = ""


@dataclass
class UserBadge:
    id: int = 0
    user_id: int = 0
    badge_id: int = 0
    earned_at: float = 0.0
    badge_code: str = ""  # joined field
    badge_name: str = ""  # joined field


@dataclass
class CookingTimer:
    id: int = 0
    recipe_id: int = 0
    label: str = ""
    duration_seconds: int = 0
    sort_order: int = 0


@dataclass
class MealPlan:
    id: int = 0
    user_id: int = 0
    date: str = ""  # YYYY-MM-DD
    meal_type: str = ""  # breakfast, lunch, dinner, snack
    recipe_id: int = 0
    note: str = ""


@dataclass
class ShoppingItem:
    id: int = 0
    user_id: int = 0
    name: str = ""
    amount: str = ""
    unit: str = ""
    checked: bool = False
    recipe_id: int | None = None


@dataclass
class BlockedUser:
    id: int = 0
    blocker_id: int = 0
    blocked_id: int = 0
    created_at: float = 0.0


@dataclass
class QA:
    id: int = 0
    recipe_id: int = 0
    user_id: int = 0
    question: str = ""
    answer: str = ""
    answered_by: int | None = None
    created_at: float = 0.0
    answered_at: float | None = None
    username: str = ""  # joined


@dataclass
class AllergyInfo:
    id: int = 0
    recipe_id: int = 0
    allergen: str = ""  # e.g. "gluten", "dairy", "nuts"


@dataclass
class DifficultyVote:
    id: int = 0
    recipe_id: int = 0
    user_id: int = 0
    vote: str = ""  # easy, medium, hard
    created_at: float = 0.0


@dataclass
class ViewHistory:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    viewed_at: float = 0.0


@dataclass
class IngredientSub:
    id: int = 0
    original: str = ""
    substitute: str = ""
    note: str = ""


@dataclass
class Challenge:
    id: int = 0
    title: str = ""
    description: str = ""
    ingredient: str = ""
    start_date: str = ""  # YYYY-MM-DD
    end_date: str = ""
    created_at: float = 0.0


@dataclass
class ChallengeEntry:
    id: int = 0
    challenge_id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    created_at: float = 0.0


@dataclass
class Poll:
    id: int = 0
    recipe_id: int = 0
    question: str = ""
    created_by: int = 0
    created_at: float = 0.0


@dataclass
class PollOption:
    id: int = 0
    poll_id: int = 0
    text: str = ""
    vote_count: int = 0


@dataclass
class PollVote:
    id: int = 0
    poll_id: int = 0
    option_id: int = 0
    user_id: int = 0


@dataclass
class RecipeTip:
    id: int = 0
    recipe_id: int = 0
    user_id: int = 0
    content: str = ""
    created_at: float = 0.0
    username: str = ""  # joined


@dataclass
class RecipeVersion:
    id: int = 0
    recipe_id: int = 0
    version_num: int = 0
    title: str = ""
    description: str = ""
    instructions: str = ""
    created_at: float = 0.0


@dataclass
class BookmarkTag:
    id: int = 0
    user_id: int = 0
    name: str = ""


@dataclass
class Equipment:
    id: int = 0
    recipe_id: int = 0
    name: str = ""


@dataclass
class UserNote:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    content: str = ""
    updated_at: float = 0.0


@dataclass
class SearchHistory:
    id: int = 0
    user_id: int = 0
    query: str = ""
    searched_at: float = 0.0


@dataclass
class ActivityLog:
    id: int = 0
    user_id: int = 0
    action: str = ""
    detail: str = ""
    created_at: float = 0.0


@dataclass
class CuratedList:
    id: int = 0
    title: str = ""
    description: str = ""
    created_by: int = 0
    created_at: float = 0.0


@dataclass
class CuratedListItem:
    id: int = 0
    list_id: int = 0
    recipe_id: int = 0
    sort_order: int = 0


@dataclass
class IngredientNutrition:
    id: int = 0
    name: str = ""
    calories_per_100g: float = 0.0
    protein_per_100g: float = 0.0
    carbs_per_100g: float = 0.0
    fat_per_100g: float = 0.0


@dataclass
class UserPreference:
    user_id: int = 0
    preferred_categories: str = ""  # comma-separated
    excluded_allergens: str = ""  # comma-separated
    max_cooking_time: int = 0
    preferred_difficulty: str = ""


@dataclass
class RecipeTranslation:
    id: int = 0
    recipe_id: int = 0
    language: str = ""  # en, ko, ja, zh
    title: str = ""
    description: str = ""


@dataclass
class PantryItem:
    id: int = 0
    user_id: int = 0
    name: str = ""
    amount: str = ""
    unit: str = ""
    expiry_date: str = ""  # YYYY-MM-DD


@dataclass
class NotificationPref:
    user_id: int = 0
    likes: bool = True
    comments: bool = True
    follows: bool = True
    challenges: bool = True


@dataclass
class AttemptLog:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    status: str = ""  # success, failed, partial
    note: str = ""
    created_at: float = 0.0


@dataclass
class Quiz:
    id: int = 0
    recipe_id: int = 0
    question: str = ""
    correct_answer: str = ""
    wrong_answers: str = ""  # pipe-separated
    created_at: float = 0.0


@dataclass
class HealthGoal:
    user_id: int = 0
    daily_calories: int = 0
    daily_protein_g: float = 0.0
    daily_carbs_g: float = 0.0
    daily_fat_g: float = 0.0


@dataclass
class RatingReview:
    id: int = 0
    rating_id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    text: str = ""
    created_at: float = 0.0


@dataclass
class IngredientGroup:
    id: int = 0
    recipe_id: int = 0
    group_name: str = ""
    sort_order: int = 0


@dataclass
class RecipeDraft:
    id: int = 0
    user_id: int = 0
    title: str = ""
    data_json: str = ""
    updated_at: float = 0.0


@dataclass
class CookingProgress:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    current_step: int = 0
    total_steps: int = 0
    started_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class RecipeSource:
    id: int = 0
    recipe_id: int = 0
    url: str = ""
    source_name: str = ""


@dataclass
class CostLog:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    amount: float = 0.0
    note: str = ""
    created_at: float = 0.0


@dataclass
class RecipeReaction:
    id: int = 0
    user_id: int = 0
    recipe_id: int = 0
    emoji: str = ""
    created_at: float = 0.0


@dataclass
class CookingPlaylist:
    id: int = 0
    user_id: int = 0
    name: str = ""
    created_at: float = 0.0


@dataclass
class PlaylistItem:
    id: int = 0
    playlist_id: int = 0
    recipe_id: int = 0
    sort_order: int = 0


@dataclass
class RecipeCertification:
    id: int = 0
    recipe_id: int = 0
    certified_by: int = 0
    certified_at: float = 0.0


@dataclass
class IngredientSeason:
    id: int = 0
    name: str = ""
    seasons: str = ""


@dataclass
class TimerPreset:
    id: int = 0
    user_id: int = 0
    name: str = ""
    timers_json: str = ""
    created_at: float = 0.0


@dataclass
class RecipeEditLog:
    id: int = 0
    recipe_id: int = 0
    user_id: int = 0
    field_name: str = ""
    old_value: str = ""
    new_value: str = ""
    edited_at: float = 0.0


@dataclass
class SocialShare:
    id: int = 0
    recipe_id: int = 0
    platform: str = ""
    shared_at: float = 0.0


@dataclass
class RecipeTemplate:
    id: int = 0
    name: str = ""
    description: str = ""
    default_data_json: str = ""
    created_at: float = 0.0


@dataclass
class PriceAlert:
    id: int = 0
    user_id: int = 0
    ingredient: str = ""
    max_price: float = 0.0
    created_at: float = 0.0


@dataclass
class CookingClass:
    id: int = 0
    title: str = ""
    description: str = ""
    instructor_id: int = 0
    scheduled_date: str = ""
    max_participants: int = 20
    created_at: float = 0.0


@dataclass
class RecipeBundle:
    id: int = 0
    name: str = ""
    description: str = ""
    created_by: int = 0
    created_at: float = 0.0


@dataclass
class MealPrep:
    id: int = 0
    user_id: int = 0
    name: str = ""
    prep_date: str = ""
    servings: int = 4
    created_at: float = 0.0


@dataclass
class JournalEntry:
    id: int = 0
    user_id: int = 0
    date: str = ""
    content: str = ""
    recipe_id: int | None = None
    mood: str = ""
    created_at: float = 0.0


# --- Unit conversion factors ---
UNIT_CONVERSIONS = {
    ("g", "oz"): 0.03527396,
    ("oz", "g"): 28.3495,
    ("ml", "cup"): 0.00422675,
    ("cup", "ml"): 236.588,
    ("tsp", "ml"): 4.92892,
    ("ml", "tsp"): 0.202884,
    ("tbsp", "ml"): 14.7868,
    ("ml", "tbsp"): 0.067628,
    ("kg", "lb"): 2.20462,
    ("lb", "kg"): 0.453592,
    ("l", "ml"): 1000,
    ("ml", "l"): 0.001,
}

RECIPE_CATEGORIES = [
    "korean", "chinese", "japanese", "western", "italian",
    "mexican", "thai", "indian", "vietnamese", "fusion", "dessert", "drink", "other",
]


# --- Point configuration ---
POINTS_RECIPE_CREATED = 10
POINTS_RECIPE_LIKED = 2
POINTS_FIRST_RECIPE_BONUS = 20
POINTS_COMMENT_WRITTEN = 3
POINTS_RATING_GIVEN = 1
POINTS_COOK_LOGGED = 2
POINTS_REPLY_WRITTEN = 1
POINTS_QA_ANSWER = 2
POINTS_CHALLENGE_COMPLETE = 5

# --- User level thresholds ---
USER_LEVELS = [
    (0, "초보 요리사"),
    (50, "견습 요리사"),
    (150, "중급 요리사"),
    (300, "고급 요리사"),
    (500, "마스터 셰프"),
    (1000, "그랜드 셰프"),
]


def hash_password(password: str, salt: str = "") -> str:
    """Hash a password with salt using SHA-256."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    salt = stored_hash.split(":")[0]
    return hash_password(password, salt) == stored_hash


class Database:
    """SQLite database manager for FridgeChef."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = str(db_path or DB_PATH)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                instructions TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                cooking_time_min INTEGER DEFAULT 0,
                servings INTEGER DEFAULT 1,
                difficulty TEXT DEFAULT 'easy' CHECK(difficulty IN ('easy', 'medium', 'hard')),
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                rating_avg REAL DEFAULT 0.0,
                rating_count INTEGER DEFAULT 0,
                bookmark_count INTEGER DEFAULT 0,
                fork_count INTEGER DEFAULT 0,
                cook_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                season TEXT DEFAULT '',
                category TEXT DEFAULT '',
                is_public INTEGER DEFAULT 1,
                scheduled_at REAL DEFAULT NULL,
                forked_from_id INTEGER DEFAULT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (author_id) REFERENCES users(id),
                FOREIGN KEY (forked_from_id) REFERENCES recipes(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amount TEXT DEFAULT '',
                unit TEXT DEFAULT '',
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS point_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name COLLATE NOCASE);
            CREATE INDEX IF NOT EXISTS idx_ingredients_recipe ON ingredients(recipe_id);
            CREATE INDEX IF NOT EXISTS idx_recipes_author ON recipes(author_id);
            CREATE INDEX IF NOT EXISTS idx_likes_user ON likes(user_id);
            CREATE INDEX IF NOT EXISTS idx_likes_recipe ON likes(recipe_id);

            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                parent_id INTEGER DEFAULT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_comments_recipe ON comments(recipe_id);
            CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id);

            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_ratings_recipe ON ratings(recipe_id);

            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);
            CREATE INDEX IF NOT EXISTS idx_bookmarks_recipe ON bookmarks(recipe_id);

            CREATE TABLE IF NOT EXISTS follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL,
                following_id INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(follower_id, following_id),
                FOREIGN KEY (follower_id) REFERENCES users(id),
                FOREIGN KEY (following_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
            CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE
            );

            CREATE TABLE IF NOT EXISTS recipe_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                UNIQUE(recipe_id, tag_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            );

            CREATE INDEX IF NOT EXISTS idx_recipe_tags_recipe ON recipe_tags(recipe_id);
            CREATE INDEX IF NOT EXISTS idx_recipe_tags_tag ON recipe_tags(tag_id);

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                target_type TEXT NOT NULL CHECK(target_type IN ('recipe', 'comment')),
                target_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'dismissed')),
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(reporter_id, target_type, target_id),
                FOREIGN KEY (reporter_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

            CREATE TABLE IF NOT EXISTS cook_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                note TEXT DEFAULT '',
                photo_url TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_cook_logs_user ON cook_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_cook_logs_recipe ON cook_logs(recipe_id);

            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_collections_user ON collections(user_id);

            CREATE TABLE IF NOT EXISTS collection_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                added_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(collection_id, recipe_id),
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                reference_id INTEGER DEFAULT 0,
                is_read INTEGER DEFAULT 0,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read);

            CREATE TABLE IF NOT EXISTS share_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                view_count INTEGER DEFAULT 0,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_share_links_token ON share_links(token);

            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                bio TEXT DEFAULT '',
                avatar_url TEXT DEFAULT '',
                website TEXT DEFAULT '',
                updated_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                caption TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_recipe_images_recipe ON recipe_images(recipe_id);

            CREATE TABLE IF NOT EXISTS nutrition_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER UNIQUE NOT NULL,
                calories INTEGER DEFAULT 0,
                protein_g REAL DEFAULT 0.0,
                carbs_g REAL DEFAULT 0.0,
                fat_g REAL DEFAULT 0.0,
                fiber_g REAL DEFAULT 0.0,
                sodium_mg REAL DEFAULT 0.0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipe_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                title TEXT DEFAULT '',
                description TEXT NOT NULL,
                image_url TEXT DEFAULT '',
                timer_minutes INTEGER DEFAULT 0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_recipe_steps_recipe ON recipe_steps(recipe_id);

            CREATE TABLE IF NOT EXISTS ingredient_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                price REAL NOT NULL,
                unit TEXT DEFAULT '',
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            );

            CREATE TABLE IF NOT EXISTS badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS user_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                badge_id INTEGER NOT NULL,
                earned_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, badge_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (badge_id) REFERENCES badges(id)
            );

            CREATE INDEX IF NOT EXISTS idx_user_badges_user ON user_badges(user_id);

            CREATE TABLE IF NOT EXISTS cooking_timers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_cooking_timers_recipe ON cooking_timers(recipe_id);

            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                meal_type TEXT NOT NULL CHECK(meal_type IN ('breakfast','lunch','dinner','snack')),
                recipe_id INTEGER NOT NULL,
                note TEXT DEFAULT '',
                UNIQUE(user_id, date, meal_type),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_meal_plans_user_date ON meal_plans(user_id, date);

            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amount TEXT DEFAULT '',
                unit TEXT DEFAULT '',
                checked INTEGER DEFAULT 0,
                recipe_id INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_shopping_user ON shopping_items(user_id);

            CREATE TABLE IF NOT EXISTS blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blocker_id INTEGER NOT NULL,
                blocked_id INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(blocker_id, blocked_id),
                FOREIGN KEY (blocker_id) REFERENCES users(id),
                FOREIGN KEY (blocked_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_qa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT DEFAULT '',
                answered_by INTEGER DEFAULT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                answered_at REAL DEFAULT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (answered_by) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_qa_recipe ON recipe_qa(recipe_id);

            CREATE TABLE IF NOT EXISTS allergy_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                allergen TEXT NOT NULL,
                UNIQUE(recipe_id, allergen),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS difficulty_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote TEXT NOT NULL CHECK(vote IN ('easy','medium','hard')),
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS view_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                viewed_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_view_history_user ON view_history(user_id);

            CREATE TABLE IF NOT EXISTS ingredient_subs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original TEXT NOT NULL COLLATE NOCASE,
                substitute TEXT NOT NULL,
                note TEXT DEFAULT '',
                UNIQUE(original, substitute)
            );

            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                ingredient TEXT DEFAULT '',
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            );

            CREATE TABLE IF NOT EXISTS challenge_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(challenge_id, user_id),
                FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );

            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS poll_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                vote_count INTEGER DEFAULT 0,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS poll_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                UNIQUE(poll_id, user_id),
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE,
                FOREIGN KEY (option_id) REFERENCES poll_options(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_tips_recipe ON recipe_tips(recipe_id);

            CREATE TABLE IF NOT EXISTS recipe_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                version_num INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                instructions TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_versions_recipe ON recipe_versions(recipe_id);

            CREATE TABLE IF NOT EXISTS bookmark_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(user_id, name),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS bookmark_tag_map (
                bookmark_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (bookmark_id, tag_id),
                FOREIGN KEY (bookmark_id) REFERENCES bookmarks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES bookmark_tags(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                updated_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                searched_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                detail TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log(user_id);

            CREATE TABLE IF NOT EXISTS curated_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_by INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS curated_list_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                sort_order INTEGER DEFAULT 0,
                UNIQUE(list_id, recipe_id),
                FOREIGN KEY (list_id) REFERENCES curated_lists(id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ingredient_nutrition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                calories_per_100g REAL DEFAULT 0,
                protein_per_100g REAL DEFAULT 0,
                carbs_per_100g REAL DEFAULT 0,
                fat_per_100g REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                preferred_categories TEXT DEFAULT '',
                excluded_allergens TEXT DEFAULT '',
                max_cooking_time INTEGER DEFAULT 0,
                preferred_difficulty TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                UNIQUE(recipe_id, language),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pantry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amount TEXT DEFAULT '',
                unit TEXT DEFAULT '',
                expiry_date TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_pantry_user ON pantry(user_id);

            CREATE TABLE IF NOT EXISTS notification_prefs (
                user_id INTEGER PRIMARY KEY,
                likes INTEGER DEFAULT 1,
                comments INTEGER DEFAULT 1,
                follows INTEGER DEFAULT 1,
                challenges INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS attempt_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('success','failed','partial')),
                note TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                wrong_answers TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS health_goals (
                user_id INTEGER PRIMARY KEY,
                daily_calories INTEGER DEFAULT 0,
                daily_protein_g REAL DEFAULT 0,
                daily_carbs_g REAL DEFAULT 0,
                daily_fat_g REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS popular_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE NOT NULL COLLATE NOCASE,
                search_count INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS rating_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rating_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ingredient_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                group_name TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipe_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                data_json TEXT NOT NULL,
                updated_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, title),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS cooking_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                current_step INTEGER DEFAULT 0,
                total_steps INTEGER DEFAULT 0,
                started_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipe_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER UNIQUE NOT NULL,
                url TEXT NOT NULL,
                source_name TEXT DEFAULT '',
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cost_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                note TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipe_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id, emoji),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cooking_playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS playlist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                sort_order INTEGER DEFAULT 0,
                UNIQUE(playlist_id, recipe_id),
                FOREIGN KEY (playlist_id) REFERENCES cooking_playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipe_certifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER UNIQUE NOT NULL,
                certified_by INTEGER NOT NULL,
                certified_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (certified_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS ingredient_seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                seasons TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS timer_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                timers_json TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, name),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT DEFAULT '',
                new_value TEXT DEFAULT '',
                edited_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS social_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                shared_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipe_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                default_data_json TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            );

            CREATE TABLE IF NOT EXISTS cooking_skills (
                user_id INTEGER PRIMARY KEY,
                skill_level TEXT NOT NULL CHECK(skill_level IN ('beginner','intermediate','advanced','expert')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS serving_preferences (
                user_id INTEGER PRIMARY KEY,
                default_servings INTEGER DEFAULT 2,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                archived_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                condition_type TEXT NOT NULL,
                condition_value INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                awarded_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, achievement_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(id)
            );

            CREATE TABLE IF NOT EXISTS hashtags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                hashtag TEXT NOT NULL,
                UNIQUE(recipe_id, hashtag),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ingredient TEXT NOT NULL,
                max_price REAL NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(user_id, ingredient),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_collaborators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'editor',
                added_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(recipe_id, user_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS cooking_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                instructor_id INTEGER NOT NULL,
                scheduled_date TEXT NOT NULL,
                max_participants INTEGER DEFAULT 20,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (instructor_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS class_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                registered_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(class_id, user_id),
                FOREIGN KEY (class_id) REFERENCES cooking_classes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_bundles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_by INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS bundle_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bundle_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                sort_order INTEGER DEFAULT 0,
                UNIQUE(bundle_id, recipe_id),
                FOREIGN KEY (bundle_id) REFERENCES recipe_bundles(id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS meal_preps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                prep_date TEXT NOT NULL,
                servings INTEGER DEFAULT 4,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS meal_prep_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prep_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                UNIQUE(prep_id, recipe_id),
                FOREIGN KEY (prep_id) REFERENCES meal_preps(id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS flavor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER UNIQUE NOT NULL,
                sweet INTEGER DEFAULT 0,
                salty INTEGER DEFAULT 0,
                sour INTEGER DEFAULT 0,
                bitter INTEGER DEFAULT 0,
                umami INTEGER DEFAULT 0,
                spicy INTEGER DEFAULT 0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS approval_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER UNIQUE NOT NULL,
                submitted_by INTEGER NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
                reviewer_id INTEGER,
                reason TEXT DEFAULT '',
                submitted_at REAL DEFAULT (strftime('%s', 'now')),
                reviewed_at REAL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (submitted_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS cooking_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                recipe_id INTEGER DEFAULT NULL,
                mood TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS ingredient_pairings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_a TEXT NOT NULL COLLATE NOCASE,
                ingredient_b TEXT NOT NULL COLLATE NOCASE,
                score INTEGER DEFAULT 5 CHECK(score BETWEEN 1 AND 10),
                UNIQUE(ingredient_a, ingredient_b)
            );

            CREATE TABLE IF NOT EXISTS mood_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                mood TEXT NOT NULL,
                UNIQUE(recipe_id, mood),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS speed_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                target_minutes INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS speed_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                actual_minutes INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(challenge_id, user_id),
                FOREIGN KEY (challenge_id) REFERENCES speed_challenges(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                message TEXT DEFAULT '',
                is_opened INTEGER DEFAULT 0,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ingredient_wiki (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                description TEXT DEFAULT '',
                tips TEXT DEFAULT '',
                storage TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now'))
            );

            CREATE TABLE IF NOT EXISTS cooking_techniques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                difficulty TEXT DEFAULT 'easy'
            );

            CREATE TABLE IF NOT EXISTS recipe_techniques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                technique_id INTEGER NOT NULL,
                UNIQUE(recipe_id, technique_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (technique_id) REFERENCES cooking_techniques(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chef_endorsements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(recipe_id, user_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS ingredient_origins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                origin TEXT NOT NULL,
                description TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                event_date TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s', 'now'))
            );

            CREATE TABLE IF NOT EXISTS event_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                UNIQUE(event_id, recipe_id),
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS group_cooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                host_id INTEGER NOT NULL,
                cook_date TEXT NOT NULL,
                max_participants INTEGER DEFAULT 8,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (host_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS group_cook_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at REAL DEFAULT (strftime('%s', 'now')),
                UNIQUE(group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES group_cooks(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT DEFAULT '',
                description TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS store_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                ingredient TEXT NOT NULL COLLATE NOCASE,
                price REAL DEFAULT 0,
                UNIQUE(store_id, ingredient),
                FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipe_stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER UNIQUE NOT NULL,
                story TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cooking_faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at REAL DEFAULT (strftime('%s', 'now'))
            );

            CREATE INDEX IF NOT EXISTS idx_rating_reviews_recipe ON rating_reviews(recipe_id);
            CREATE INDEX IF NOT EXISTS idx_ingredient_groups_recipe ON ingredient_groups(recipe_id);
            CREATE INDEX IF NOT EXISTS idx_cost_logs_user ON cost_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_recipe_reactions_recipe ON recipe_reactions(recipe_id);
            CREATE INDEX IF NOT EXISTS idx_hashtags_hashtag ON hashtags(hashtag);
            CREATE INDEX IF NOT EXISTS idx_mood_tags_mood ON mood_tags(mood);

            -- Seed default badges
            INSERT OR IGNORE INTO badges (code, name, description, icon) VALUES
                ('first_recipe', '첫 레시피', '첫 번째 레시피를 등록했습니다', '🍳'),
                ('recipe_10', '레시피 마스터', '레시피 10개를 등록했습니다', '👨‍🍳'),
                ('liked_50', '인기 셰프', '좋아요 50개를 받았습니다', '❤️'),
                ('cook_5', '요리 실천가', '5번 요리를 완료했습니다', '🔥'),
                ('follower_10', '인플루언서', '팔로워 10명을 달성했습니다', '⭐'),
                ('comment_20', '소통왕', '댓글 20개를 작성했습니다', '💬'),
                ('collector', '컬렉터', '첫 컬렉션을 만들었습니다', '📁'),
                ('forker', '리믹서', '첫 레시피 포크를 했습니다', '🔀'),
                ('rating_10', '평가왕', '별점 10개를 남겼습니다', '⭐'),
                ('points_100', '포인트 부자', '포인트 100점을 달성했습니다', '💰');
        """)
        conn.commit()
        conn.close()

    # --- User operations ---

    def create_user(self, username: str, email: str, password: str) -> User:
        conn = self._get_conn()
        pw_hash = hash_password(password)
        now = time.time()
        try:
            cur = conn.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, email, pw_hash, now),
            )
            conn.commit()
            return User(id=cur.lastrowid, username=username, email=email,
                        password_hash=pw_hash, points=0, created_at=now)
        except sqlite3.IntegrityError as e:
            raise ValueError(f"User already exists: {e}") from e
        finally:
            conn.close()

    def get_user(self, user_id: int) -> User | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return User(**dict(row))

    def get_user_by_username(self, username: str) -> User | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if not row:
            return None
        return User(**dict(row))

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.get_user_by_username(username)
        if user and verify_password(password, user.password_hash):
            return user
        return None

    def update_points(self, user_id: int, amount: int, reason: str) -> int:
        conn = self._get_conn()
        conn.execute(
            "UPDATE users SET points = points + ? WHERE id = ?",
            (amount, user_id),
        )
        conn.execute(
            "INSERT INTO point_history (user_id, amount, reason) VALUES (?, ?, ?)",
            (user_id, amount, reason),
        )
        conn.commit()
        row = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return row["points"] if row else 0

    def get_point_history(self, user_id: int, limit: int = 50) -> list[PointHistory]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM point_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [PointHistory(**dict(r)) for r in rows]

    def get_leaderboard(self, limit: int = 20) -> list[User]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM users WHERE is_active = 1 ORDER BY points DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [User(**dict(r)) for r in rows]

    # --- Recipe operations ---

    def create_recipe(
        self,
        title: str,
        description: str,
        instructions: str,
        author_id: int,
        ingredients: list[dict[str, str]],
        cooking_time_min: int = 0,
        servings: int = 1,
        difficulty: str = "easy",
    ) -> Recipe:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            """INSERT INTO recipes (title, description, instructions, author_id,
               cooking_time_min, servings, difficulty, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, instructions, author_id,
             cooking_time_min, servings, difficulty, now),
        )
        recipe_id = cur.lastrowid

        for ing in ingredients:
            conn.execute(
                "INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
                (recipe_id, ing["name"], ing.get("amount", ""), ing.get("unit", "")),
            )

        conn.commit()
        conn.close()

        # Award points
        is_first = self._is_first_recipe(author_id)
        points = POINTS_RECIPE_CREATED
        reason = "레시피 등록"
        if is_first:
            points += POINTS_FIRST_RECIPE_BONUS
            reason = "첫 레시피 등록 보너스"
        self.update_points(author_id, points, reason)

        return Recipe(
            id=recipe_id, title=title, description=description,
            instructions=instructions, author_id=author_id,
            cooking_time_min=cooking_time_min, servings=servings,
            difficulty=difficulty, created_at=now,
        )

    def _is_first_recipe(self, author_id: int) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM recipes WHERE author_id = ?",
            (author_id,),
        ).fetchone()
        conn.close()
        return row["cnt"] <= 1

    def get_recipe(self, recipe_id: int) -> Recipe | None:
        conn = self._get_conn()
        row = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM recipes r JOIN users u ON r.author_id = u.id
               WHERE r.id = ?""",
            (recipe_id,),
        ).fetchone()
        conn.close()
        if not row:
            return None
        return Recipe(**dict(row))

    def get_recipe_ingredients(self, recipe_id: int) -> list[Ingredient]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM ingredients WHERE recipe_id = ?", (recipe_id,),
        ).fetchall()
        conn.close()
        return [Ingredient(**dict(r)) for r in rows]

    def list_recipes(
        self, offset: int = 0, limit: int = 20, sort_by: str = "recent",
    ) -> list[Recipe]:
        order = "r.created_at DESC"
        if sort_by == "popular":
            order = "r.like_count DESC, r.created_at DESC"
        elif sort_by == "cooking_time":
            order = "r.cooking_time_min ASC"

        conn = self._get_conn()
        rows = conn.execute(
            f"""SELECT r.*, u.username as author_name
                FROM recipes r JOIN users u ON r.author_id = u.id
                ORDER BY {order} LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_user_recipes(self, author_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM recipes r JOIN users u ON r.author_id = u.id
               WHERE r.author_id = ? ORDER BY r.created_at DESC""",
            (author_id,),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def delete_recipe(self, recipe_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        result = conn.execute(
            "DELETE FROM recipes WHERE id = ? AND author_id = ?",
            (recipe_id, user_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    # --- Ingredient matching (core feature) ---

    def find_recipes_by_ingredients(
        self,
        ingredient_names: list[str],
        min_match_ratio: float = 0.5,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Find recipes that can be made with given ingredients.

        Returns recipes sorted by ingredient match ratio (highest first).
        A recipe with 3/4 matching ingredients scores 0.75.
        """
        if not ingredient_names:
            return []

        conn = self._get_conn()

        # Normalize ingredient names for matching
        normalized = [name.strip().lower() for name in ingredient_names]

        # Build LIKE conditions for fuzzy matching
        like_conditions = " OR ".join(
            "LOWER(i.name) LIKE ?" for _ in normalized
        )
        like_params = [f"%{name}%" for name in normalized]

        # Find recipes with matching ingredients and calculate match ratio
        query = f"""
            WITH recipe_ingredient_count AS (
                SELECT recipe_id, COUNT(*) as total_ingredients
                FROM ingredients
                GROUP BY recipe_id
            ),
            matched_ingredients AS (
                SELECT i.recipe_id, COUNT(DISTINCT i.name) as matched_count
                FROM ingredients i
                WHERE {like_conditions}
                GROUP BY i.recipe_id
            )
            SELECT r.*, u.username as author_name,
                   m.matched_count,
                   ric.total_ingredients,
                   CAST(m.matched_count AS REAL) / ric.total_ingredients as match_ratio
            FROM matched_ingredients m
            JOIN recipe_ingredient_count ric ON m.recipe_id = ric.recipe_id
            JOIN recipes r ON r.id = m.recipe_id
            JOIN users u ON r.author_id = u.id
            WHERE CAST(m.matched_count AS REAL) / ric.total_ingredients >= ?
            ORDER BY match_ratio DESC, r.like_count DESC
            LIMIT ?
        """

        rows = conn.execute(query, [*like_params, min_match_ratio, limit]).fetchall()
        conn.close()

        results = []
        for row in rows:
            d = dict(row)
            recipe = Recipe(
                id=d["id"], title=d["title"], description=d["description"],
                instructions=d["instructions"], author_id=d["author_id"],
                cooking_time_min=d["cooking_time_min"], servings=d["servings"],
                difficulty=d["difficulty"], like_count=d["like_count"],
                created_at=d["created_at"], author_name=d["author_name"],
            )
            results.append({
                "recipe": recipe,
                "matched_count": d["matched_count"],
                "total_ingredients": d["total_ingredients"],
                "match_ratio": round(d["match_ratio"], 2),
                "missing_count": d["total_ingredients"] - d["matched_count"],
            })

        return results

    # --- Like operations ---

    def toggle_like(self, user_id: int, recipe_id: int) -> dict[str, Any]:
        """Toggle like on a recipe. Returns new like status and count."""
        conn = self._get_conn()

        existing = conn.execute(
            "SELECT id FROM likes WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        ).fetchone()

        recipe = self.get_recipe(recipe_id)
        if not recipe:
            conn.close()
            raise ValueError("Recipe not found")

        # Prevent self-likes from awarding points (but allow the like itself)
        is_own_recipe = recipe.author_id == user_id

        if existing:
            # Unlike
            conn.execute("DELETE FROM likes WHERE user_id = ? AND recipe_id = ?",
                         (user_id, recipe_id))
            conn.execute("UPDATE recipes SET like_count = MAX(0, like_count - 1) WHERE id = ?",
                         (recipe_id,))
            conn.commit()
            new_count = conn.execute(
                "SELECT like_count FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()["like_count"]
            conn.close()

            if not is_own_recipe:
                self.update_points(recipe.author_id, -POINTS_RECIPE_LIKED, "좋아요 취소")

            return {"liked": False, "like_count": new_count}
        else:
            # Like
            conn.execute(
                "INSERT INTO likes (user_id, recipe_id) VALUES (?, ?)",
                (user_id, recipe_id),
            )
            conn.execute("UPDATE recipes SET like_count = like_count + 1 WHERE id = ?",
                         (recipe_id,))
            conn.commit()
            new_count = conn.execute(
                "SELECT like_count FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()["like_count"]
            conn.close()

            if not is_own_recipe:
                self.update_points(recipe.author_id, POINTS_RECIPE_LIKED, "레시피 좋아요 받음")

            return {"liked": True, "like_count": new_count}

    def is_liked(self, user_id: int, recipe_id: int) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id FROM likes WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        ).fetchone()
        conn.close()
        return row is not None

    def get_user_likes(self, user_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM likes l
               JOIN recipes r ON l.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE l.user_id = ?
               ORDER BY l.created_at DESC""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Comment operations ---

    def add_comment(self, recipe_id: int, user_id: int, content: str) -> Comment:
        """Add a comment to a recipe. Awards points to the commenter."""
        content = content.strip()
        if not content:
            raise ValueError("댓글 내용을 입력하세요")
        if len(content) > 2000:
            raise ValueError("댓글은 2000자 이하로 작성하세요")

        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")

        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO comments (recipe_id, user_id, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (recipe_id, user_id, content, now, now),
        )
        conn.execute(
            "UPDATE recipes SET comment_count = comment_count + 1 WHERE id = ?",
            (recipe_id,),
        )
        conn.commit()
        comment_id = cur.lastrowid
        conn.close()

        self.update_points(user_id, POINTS_COMMENT_WRITTEN, "댓글 작성")

        return Comment(
            id=comment_id, recipe_id=recipe_id, user_id=user_id,
            content=content, created_at=now, updated_at=now,
        )

    def get_comments(
        self, recipe_id: int, offset: int = 0, limit: int = 50,
    ) -> list[Comment]:
        """Get comments for a recipe, newest first."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT c.*, u.username
               FROM comments c JOIN users u ON c.user_id = u.id
               WHERE c.recipe_id = ?
               ORDER BY c.created_at DESC LIMIT ? OFFSET ?""",
            (recipe_id, limit, offset),
        ).fetchall()
        conn.close()
        return [Comment(**dict(r)) for r in rows]

    def update_comment(self, comment_id: int, user_id: int, content: str) -> Comment | None:
        """Update a comment. Only the author can edit."""
        content = content.strip()
        if not content:
            raise ValueError("댓글 내용을 입력하세요")
        if len(content) > 2000:
            raise ValueError("댓글은 2000자 이하로 작성하세요")

        conn = self._get_conn()
        now = time.time()
        result = conn.execute(
            "UPDATE comments SET content = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (content, now, comment_id, user_id),
        )
        conn.commit()
        if result.rowcount == 0:
            conn.close()
            return None

        row = conn.execute(
            """SELECT c.*, u.username
               FROM comments c JOIN users u ON c.user_id = u.id
               WHERE c.id = ?""",
            (comment_id,),
        ).fetchone()
        conn.close()
        return Comment(**dict(row)) if row else None

    def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """Delete a comment. Only the author can delete."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT recipe_id FROM comments WHERE id = ? AND user_id = ?",
            (comment_id, user_id),
        ).fetchone()
        if not row:
            conn.close()
            return False

        recipe_id = row["recipe_id"]
        conn.execute("DELETE FROM comments WHERE id = ? AND user_id = ?",
                      (comment_id, user_id))
        conn.execute(
            "UPDATE recipes SET comment_count = MAX(0, comment_count - 1) WHERE id = ?",
            (recipe_id,),
        )
        conn.commit()
        conn.close()
        return True

    def get_comment_count(self, recipe_id: int) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM comments WHERE recipe_id = ?",
            (recipe_id,),
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0

    # --- Rating operations ---

    def rate_recipe(self, recipe_id: int, user_id: int, score: int) -> dict:
        """Rate a recipe 1~5. Updates if already rated. Returns new average."""
        if not 1 <= score <= 5:
            raise ValueError("별점은 1~5 사이여야 합니다")

        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        if recipe.author_id == user_id:
            raise ValueError("본인 레시피에는 별점을 줄 수 없습니다")

        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id, score FROM ratings WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        ).fetchone()

        now = time.time()
        is_new = existing is None

        if existing:
            conn.execute(
                "UPDATE ratings SET score = ?, created_at = ? WHERE id = ?",
                (score, now, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO ratings (recipe_id, user_id, score, created_at) VALUES (?, ?, ?, ?)",
                (recipe_id, user_id, score, now),
            )

        # Recalculate average
        row = conn.execute(
            "SELECT AVG(score) as avg_score, COUNT(*) as cnt FROM ratings WHERE recipe_id = ?",
            (recipe_id,),
        ).fetchone()
        new_avg = round(row["avg_score"], 2) if row["avg_score"] else 0.0
        new_count = row["cnt"]

        conn.execute(
            "UPDATE recipes SET rating_avg = ?, rating_count = ? WHERE id = ?",
            (new_avg, new_count, recipe_id),
        )
        conn.commit()
        conn.close()

        if is_new:
            self.update_points(user_id, POINTS_RATING_GIVEN, "별점 평가")

        return {
            "score": score,
            "is_new": is_new,
            "rating_avg": new_avg,
            "rating_count": new_count,
        }

    def get_user_rating(self, recipe_id: int, user_id: int) -> int | None:
        """Get a user's rating for a recipe, or None."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT score FROM ratings WHERE recipe_id = ? AND user_id = ?",
            (recipe_id, user_id),
        ).fetchone()
        conn.close()
        return row["score"] if row else None

    def get_recipe_ratings(self, recipe_id: int) -> dict:
        """Get rating distribution for a recipe."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT score, COUNT(*) as cnt FROM ratings WHERE recipe_id = ? GROUP BY score",
            (recipe_id,),
        ).fetchall()
        total = conn.execute(
            "SELECT AVG(score) as avg, COUNT(*) as cnt FROM ratings WHERE recipe_id = ?",
            (recipe_id,),
        ).fetchone()
        conn.close()

        distribution = {i: 0 for i in range(1, 6)}
        for row in rows:
            distribution[row["score"]] = row["cnt"]

        return {
            "average": round(total["avg"], 2) if total["avg"] else 0.0,
            "count": total["cnt"],
            "distribution": distribution,
        }

    # --- Bookmark operations ---

    def toggle_bookmark(self, user_id: int, recipe_id: int) -> dict[str, Any]:
        """Toggle bookmark on a recipe. Returns new bookmark status and count."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")

        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM bookmarks WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        ).fetchone()

        if existing:
            conn.execute("DELETE FROM bookmarks WHERE user_id = ? AND recipe_id = ?",
                         (user_id, recipe_id))
            conn.execute("UPDATE recipes SET bookmark_count = MAX(0, bookmark_count - 1) WHERE id = ?",
                         (recipe_id,))
            conn.commit()
            new_count = conn.execute(
                "SELECT bookmark_count FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()["bookmark_count"]
            conn.close()
            return {"bookmarked": False, "bookmark_count": new_count}
        else:
            now = time.time()
            conn.execute(
                "INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (?, ?, ?)",
                (user_id, recipe_id, now),
            )
            conn.execute("UPDATE recipes SET bookmark_count = bookmark_count + 1 WHERE id = ?",
                         (recipe_id,))
            conn.commit()
            new_count = conn.execute(
                "SELECT bookmark_count FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()["bookmark_count"]
            conn.close()
            return {"bookmarked": True, "bookmark_count": new_count}

    def is_bookmarked(self, user_id: int, recipe_id: int) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id FROM bookmarks WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id),
        ).fetchone()
        conn.close()
        return row is not None

    def get_user_bookmarks(self, user_id: int) -> list[Recipe]:
        """Get all bookmarked recipes for a user, newest first."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM bookmarks b
               JOIN recipes r ON b.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE b.user_id = ?
               ORDER BY b.created_at DESC""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Follow operations (Feature 1) ---

    def toggle_follow(self, follower_id: int, following_id: int) -> dict[str, Any]:
        """Follow or unfollow a user."""
        if follower_id == following_id:
            raise ValueError("자기 자신을 팔로우할 수 없습니다")

        target = self.get_user(following_id)
        if not target:
            raise ValueError("유저를 찾을 수 없습니다")

        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM follows WHERE follower_id = ? AND following_id = ?",
            (follower_id, following_id),
        ).fetchone()

        if existing:
            conn.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
                         (follower_id, following_id))
            conn.commit()
            conn.close()
            return {"following": False}
        else:
            now = time.time()
            conn.execute(
                "INSERT INTO follows (follower_id, following_id, created_at) VALUES (?, ?, ?)",
                (follower_id, following_id, now),
            )
            conn.commit()
            conn.close()
            self._notify(following_id, "follow", f"새로운 팔로워가 생겼습니다", follower_id)
            return {"following": True}

    def is_following(self, follower_id: int, following_id: int) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id FROM follows WHERE follower_id = ? AND following_id = ?",
            (follower_id, following_id),
        ).fetchone()
        conn.close()
        return row is not None

    def get_followers(self, user_id: int) -> list[User]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT u.* FROM follows f
               JOIN users u ON f.follower_id = u.id
               WHERE f.following_id = ? ORDER BY f.created_at DESC""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [User(**dict(r)) for r in rows]

    def get_following(self, user_id: int) -> list[User]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT u.* FROM follows f
               JOIN users u ON f.following_id = u.id
               WHERE f.follower_id = ? ORDER BY f.created_at DESC""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [User(**dict(r)) for r in rows]

    def get_follower_count(self, user_id: int) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (user_id,),
        ).fetchone()
        conn.close()
        return row["cnt"]

    def get_following_count(self, user_id: int) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM follows WHERE follower_id = ?", (user_id,),
        ).fetchone()
        conn.close()
        return row["cnt"]

    def get_following_recipes(self, user_id: int, limit: int = 50) -> list[Recipe]:
        """Get recent recipes from users I follow (feed)."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM recipes r
               JOIN users u ON r.author_id = u.id
               JOIN follows f ON f.following_id = r.author_id
               WHERE f.follower_id = ?
               ORDER BY r.created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Tag operations (Feature 2) ---

    def _get_or_create_tag(self, conn: sqlite3.Connection, tag_name: str) -> int:
        tag_name = tag_name.strip().lower()
        row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        return cur.lastrowid

    def set_recipe_tags(self, recipe_id: int, tag_names: list[str]) -> list[str]:
        """Set tags for a recipe (replaces existing)."""
        conn = self._get_conn()
        conn.execute("DELETE FROM recipe_tags WHERE recipe_id = ?", (recipe_id,))
        result_tags = []
        for name in tag_names:
            name = name.strip().lower()
            if not name:
                continue
            tag_id = self._get_or_create_tag(conn, name)
            conn.execute(
                "INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id) VALUES (?, ?)",
                (recipe_id, tag_id),
            )
            result_tags.append(name)
        conn.commit()
        conn.close()
        return result_tags

    def get_recipe_tags(self, recipe_id: int) -> list[str]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT t.name FROM recipe_tags rt
               JOIN tags t ON rt.tag_id = t.id
               WHERE rt.recipe_id = ?
               ORDER BY t.name""",
            (recipe_id,),
        ).fetchall()
        conn.close()
        return [row["name"] for row in rows]

    def find_recipes_by_tag(self, tag_name: str, limit: int = 50) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM recipe_tags rt
               JOIN tags t ON rt.tag_id = t.id
               JOIN recipes r ON rt.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE t.name = ?
               ORDER BY r.created_at DESC LIMIT ?""",
            (tag_name.strip().lower(), limit),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_popular_tags(self, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT t.name, COUNT(*) as recipe_count
               FROM recipe_tags rt JOIN tags t ON rt.tag_id = t.id
               GROUP BY t.id ORDER BY recipe_count DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        return [{"name": r["name"], "count": r["recipe_count"]} for r in rows]

    # --- Search operations (Feature 3) ---

    def search_recipes(self, query: str, limit: int = 50) -> list[Recipe]:
        """Full-text search on recipe title and description."""
        query = query.strip()
        if not query:
            return []
        conn = self._get_conn()
        pattern = f"%{query}%"
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM recipes r JOIN users u ON r.author_id = u.id
               WHERE r.title LIKE ? OR r.description LIKE ?
               ORDER BY r.like_count DESC, r.created_at DESC LIMIT ?""",
            (pattern, pattern, limit),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Report operations (Feature 4) ---

    def create_report(self, reporter_id: int, target_type: str, target_id: int, reason: str) -> Report:
        reason = reason.strip()
        if not reason:
            raise ValueError("신고 사유를 입력하세요")
        if target_type not in ("recipe", "comment"):
            raise ValueError("잘못된 신고 유형입니다")
        if len(reason) > 1000:
            raise ValueError("신고 사유는 1000자 이하로 작성하세요")

        conn = self._get_conn()
        now = time.time()
        try:
            cur = conn.execute(
                "INSERT INTO reports (reporter_id, target_type, target_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                (reporter_id, target_type, target_id, reason, now),
            )
            conn.commit()
            report_id = cur.lastrowid
            conn.close()
            return Report(id=report_id, reporter_id=reporter_id, target_type=target_type,
                          target_id=target_id, reason=reason, status="pending", created_at=now)
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 신고한 항목입니다")

    def get_reports(self, status: str = "pending", limit: int = 50) -> list[Report]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM reports WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
        conn.close()
        return [Report(**dict(r)) for r in rows]

    def update_report_status(self, report_id: int, status: str) -> bool:
        if status not in ("pending", "reviewed", "dismissed"):
            raise ValueError("잘못된 상태입니다")
        conn = self._get_conn()
        result = conn.execute(
            "UPDATE reports SET status = ? WHERE id = ?", (status, report_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    # --- Fork operations (Feature 5) ---

    def fork_recipe(self, recipe_id: int, user_id: int, title: str | None = None) -> Recipe:
        """Fork (remix) a recipe, creating a copy under a new user."""
        original = self.get_recipe(recipe_id)
        if not original:
            raise ValueError("원본 레시피를 찾을 수 없습니다")

        ingredients = self.get_recipe_ingredients(recipe_id)
        ing_list = [{"name": i.name, "amount": i.amount, "unit": i.unit} for i in ingredients]

        fork_title = title or f"{original.title} (리믹스)"

        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            """INSERT INTO recipes (title, description, instructions, author_id,
               cooking_time_min, servings, difficulty, forked_from_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fork_title, original.description, original.instructions, user_id,
             original.cooking_time_min, original.servings, original.difficulty,
             recipe_id, now),
        )
        new_id = cur.lastrowid
        for ing in ing_list:
            conn.execute(
                "INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
                (new_id, ing["name"], ing.get("amount", ""), ing.get("unit", "")),
            )
        conn.execute(
            "UPDATE recipes SET fork_count = fork_count + 1 WHERE id = ?", (recipe_id,),
        )
        conn.commit()
        conn.close()

        # Copy tags
        tags = self.get_recipe_tags(recipe_id)
        if tags:
            self.set_recipe_tags(new_id, tags)

        # Points for creating recipe
        is_first = self._is_first_recipe(user_id)
        points = POINTS_RECIPE_CREATED
        reason = "레시피 포크"
        if is_first:
            points += POINTS_FIRST_RECIPE_BONUS
            reason = "첫 레시피 포크 보너스"
        self.update_points(user_id, points, reason)

        return Recipe(
            id=new_id, title=fork_title, description=original.description,
            instructions=original.instructions, author_id=user_id,
            cooking_time_min=original.cooking_time_min, servings=original.servings,
            difficulty=original.difficulty, forked_from_id=recipe_id, created_at=now,
        )

    # --- Weekly Popular (Feature 6) ---

    def get_weekly_popular(self, limit: int = 20) -> list[Recipe]:
        """Get most popular recipes from the last 7 days based on likes."""
        week_ago = time.time() - 7 * 86400
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name,
                      COUNT(l.id) as recent_likes
               FROM recipes r
               JOIN users u ON r.author_id = u.id
               LEFT JOIN likes l ON l.recipe_id = r.id AND l.created_at >= ?
               WHERE r.created_at >= ?
               GROUP BY r.id
               ORDER BY recent_likes DESC, r.rating_avg DESC
               LIMIT ?""",
            (week_ago, week_ago, limit),
        ).fetchall()
        conn.close()
        return [Recipe(**{k: v for k, v in dict(r).items() if k != "recent_likes"}) for r in rows]

    # --- Cook Log operations (Feature 7) ---

    def add_cook_log(self, user_id: int, recipe_id: int, note: str = "", photo_url: str = "") -> CookLog:
        """Log that a user cooked a recipe. Awards points."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")

        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO cook_logs (user_id, recipe_id, note, photo_url, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, recipe_id, note.strip(), photo_url.strip(), now),
        )
        conn.execute(
            "UPDATE recipes SET cook_count = cook_count + 1 WHERE id = ?", (recipe_id,),
        )
        conn.commit()
        log_id = cur.lastrowid
        conn.close()

        self.update_points(user_id, POINTS_COOK_LOGGED, "요리 완료 기록")

        return CookLog(id=log_id, user_id=user_id, recipe_id=recipe_id,
                       note=note.strip(), photo_url=photo_url.strip(), created_at=now)

    def get_cook_logs(self, recipe_id: int, limit: int = 50) -> list[CookLog]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT cl.*, u.username FROM cook_logs cl
               JOIN users u ON cl.user_id = u.id
               WHERE cl.recipe_id = ? ORDER BY cl.created_at DESC LIMIT ?""",
            (recipe_id, limit),
        ).fetchall()
        conn.close()
        return [CookLog(**dict(r)) for r in rows]

    def get_user_cook_logs(self, user_id: int, limit: int = 50) -> list[CookLog]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT cl.*, u.username FROM cook_logs cl
               JOIN users u ON cl.user_id = u.id
               WHERE cl.user_id = ? ORDER BY cl.created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [CookLog(**dict(r)) for r in rows]

    # --- Collection operations (Feature 8) ---

    def create_collection(self, user_id: int, name: str, description: str = "") -> Collection:
        name = name.strip()
        if not name:
            raise ValueError("컬렉션 이름을 입력하세요")
        if len(name) > 100:
            raise ValueError("컬렉션 이름은 100자 이하로 작성하세요")

        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO collections (user_id, name, description, created_at) VALUES (?, ?, ?, ?)",
            (user_id, name, description.strip(), now),
        )
        conn.commit()
        coll_id = cur.lastrowid
        conn.close()
        return Collection(id=coll_id, user_id=user_id, name=name,
                          description=description.strip(), created_at=now)

    def get_user_collections(self, user_id: int) -> list[Collection]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM collections WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        conn.close()
        return [Collection(**dict(r)) for r in rows]

    def delete_collection(self, collection_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        result = conn.execute(
            "DELETE FROM collections WHERE id = ? AND user_id = ?",
            (collection_id, user_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def add_to_collection(self, collection_id: int, recipe_id: int, user_id: int) -> bool:
        """Add a recipe to a collection (owner only)."""
        conn = self._get_conn()
        owner = conn.execute(
            "SELECT user_id FROM collections WHERE id = ?", (collection_id,),
        ).fetchone()
        if not owner or owner["user_id"] != user_id:
            conn.close()
            raise ValueError("컬렉션을 찾을 수 없거나 권한이 없습니다")
        now = time.time()
        try:
            conn.execute(
                "INSERT INTO collection_items (collection_id, recipe_id, added_at) VALUES (?, ?, ?)",
                (collection_id, recipe_id, now),
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 컬렉션에 추가된 레시피입니다")

    def remove_from_collection(self, collection_id: int, recipe_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        owner = conn.execute(
            "SELECT user_id FROM collections WHERE id = ?", (collection_id,),
        ).fetchone()
        if not owner or owner["user_id"] != user_id:
            conn.close()
            return False
        result = conn.execute(
            "DELETE FROM collection_items WHERE collection_id = ? AND recipe_id = ?",
            (collection_id, recipe_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def get_collection_recipes(self, collection_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM collection_items ci
               JOIN recipes r ON ci.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE ci.collection_id = ?
               ORDER BY ci.added_at DESC""",
            (collection_id,),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Notification operations (Feature 9) ---

    def _notify(self, user_id: int, ntype: str, message: str, reference_id: int = 0) -> None:
        """Internal helper to create a notification."""
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            "INSERT INTO notifications (user_id, type, message, reference_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, ntype, message, reference_id, now),
        )
        conn.commit()
        conn.close()

    def get_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> list[Notification]:
        conn = self._get_conn()
        where = "WHERE n.user_id = ?"
        params: list = [user_id]
        if unread_only:
            where += " AND n.is_read = 0"
        rows = conn.execute(
            f"SELECT * FROM notifications n {where} ORDER BY n.created_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        conn.close()
        return [Notification(**dict(r)) for r in rows]

    def mark_notifications_read(self, user_id: int, notification_ids: list[int] | None = None) -> int:
        """Mark notifications as read. If ids is None, mark all."""
        conn = self._get_conn()
        if notification_ids:
            placeholders = ",".join("?" for _ in notification_ids)
            result = conn.execute(
                f"UPDATE notifications SET is_read = 1 WHERE user_id = ? AND id IN ({placeholders})",
                (user_id, *notification_ids),
            )
        else:
            result = conn.execute(
                "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                (user_id,),
            )
        conn.commit()
        conn.close()
        return result.rowcount

    def get_unread_count(self, user_id: int) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,),
        ).fetchone()
        conn.close()
        return row["cnt"]

    # --- Share Link operations (Feature 10) ---

    def create_share_link(self, recipe_id: int) -> ShareLink:
        """Create a shareable link token for a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")

        conn = self._get_conn()
        # Check existing
        existing = conn.execute(
            "SELECT * FROM share_links WHERE recipe_id = ?", (recipe_id,),
        ).fetchone()
        if existing:
            conn.close()
            return ShareLink(**dict(existing))

        token = secrets.token_urlsafe(16)
        now = time.time()
        cur = conn.execute(
            "INSERT INTO share_links (recipe_id, token, created_at) VALUES (?, ?, ?)",
            (recipe_id, token, now),
        )
        conn.commit()
        link_id = cur.lastrowid
        conn.close()
        return ShareLink(id=link_id, recipe_id=recipe_id, token=token,
                         view_count=0, created_at=now)

    def get_recipe_by_share_token(self, token: str) -> Recipe | None:
        """Get a recipe via share token and increment view count."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT recipe_id FROM share_links WHERE token = ?", (token,),
        ).fetchone()
        if not row:
            conn.close()
            return None
        recipe_id = row["recipe_id"]
        conn.execute(
            "UPDATE share_links SET view_count = view_count + 1 WHERE token = ?",
            (token,),
        )
        conn.commit()
        conn.close()
        return self.get_recipe(recipe_id)

    def get_share_link(self, recipe_id: int) -> ShareLink | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM share_links WHERE recipe_id = ?", (recipe_id,),
        ).fetchone()
        conn.close()
        return ShareLink(**dict(row)) if row else None

    # --- Reply / Nested Comment operations (Feature 11) ---

    def add_reply(self, comment_id: int, user_id: int, content: str) -> Comment:
        """Add a reply to a comment. The reply is a Comment with parent_id set."""
        content = content.strip()
        if not content:
            raise ValueError("답글 내용을 입력하세요")
        if len(content) > 2000:
            raise ValueError("답글은 2000자 이하로 작성하세요")

        conn = self._get_conn()
        parent = conn.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
        if not parent:
            conn.close()
            raise ValueError("원본 댓글을 찾을 수 없습니다")

        recipe_id = parent["recipe_id"]
        now = time.time()
        cur = conn.execute(
            "INSERT INTO comments (recipe_id, user_id, content, parent_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (recipe_id, user_id, content, comment_id, now, now),
        )
        conn.execute(
            "UPDATE recipes SET comment_count = comment_count + 1 WHERE id = ?",
            (recipe_id,),
        )
        conn.commit()
        reply_id = cur.lastrowid
        conn.close()

        self.update_points(user_id, POINTS_REPLY_WRITTEN, "답글 작성")

        return Comment(
            id=reply_id, recipe_id=recipe_id, user_id=user_id,
            content=content, parent_id=comment_id, created_at=now, updated_at=now,
        )

    def get_replies(self, comment_id: int) -> list[Comment]:
        """Get all replies to a comment."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT c.*, u.username
               FROM comments c JOIN users u ON c.user_id = u.id
               WHERE c.parent_id = ?
               ORDER BY c.created_at ASC""",
            (comment_id,),
        ).fetchall()
        conn.close()
        return [Comment(**dict(r)) for r in rows]

    def get_reply_count(self, comment_id: int) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM comments WHERE parent_id = ?", (comment_id,),
        ).fetchone()
        conn.close()
        return row["cnt"]

    # --- User Profile operations (Feature 12) ---

    def update_profile(self, user_id: int, bio: str = "", avatar_url: str = "", website: str = "") -> UserProfile:
        """Create or update user profile."""
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO user_profiles (user_id, bio, avatar_url, website, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET bio=?, avatar_url=?, website=?, updated_at=?""",
            (user_id, bio.strip(), avatar_url.strip(), website.strip(), now,
             bio.strip(), avatar_url.strip(), website.strip(), now),
        )
        conn.commit()
        conn.close()
        return UserProfile(user_id=user_id, bio=bio.strip(), avatar_url=avatar_url.strip(),
                           website=website.strip(), updated_at=now)

    def get_profile(self, user_id: int) -> UserProfile | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return UserProfile(**dict(row))

    def get_user_detail(self, user_id: int) -> dict | None:
        """Get user info + profile + stats in one call."""
        user = self.get_user(user_id)
        if not user:
            return None
        profile = self.get_profile(user_id) or UserProfile(user_id=user_id)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "points": user.points,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "website": profile.website,
            "follower_count": self.get_follower_count(user_id),
            "following_count": self.get_following_count(user_id),
            "recipe_count": len(self.get_user_recipes(user_id)),
            "badges": [{"code": b.badge_code, "name": b.badge_name} for b in self.get_user_badges(user_id)],
            "created_at": user.created_at,
        }

    # --- Recipe Image operations (Feature 13) ---

    def add_recipe_image(self, recipe_id: int, image_url: str, caption: str = "", sort_order: int = 0) -> RecipeImage:
        if not image_url.strip():
            raise ValueError("이미지 URL을 입력하세요")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO recipe_images (recipe_id, image_url, caption, sort_order, created_at) VALUES (?, ?, ?, ?, ?)",
            (recipe_id, image_url.strip(), caption.strip(), sort_order, now),
        )
        conn.commit()
        img_id = cur.lastrowid
        conn.close()
        return RecipeImage(id=img_id, recipe_id=recipe_id, image_url=image_url.strip(),
                           caption=caption.strip(), sort_order=sort_order, created_at=now)

    def get_recipe_images(self, recipe_id: int) -> list[RecipeImage]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM recipe_images WHERE recipe_id = ? ORDER BY sort_order, id",
            (recipe_id,),
        ).fetchall()
        conn.close()
        return [RecipeImage(**dict(r)) for r in rows]

    def delete_recipe_image(self, image_id: int, user_id: int) -> bool:
        """Delete an image. Only recipe author can delete."""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT ri.id FROM recipe_images ri
               JOIN recipes r ON ri.recipe_id = r.id
               WHERE ri.id = ? AND r.author_id = ?""",
            (image_id, user_id),
        ).fetchone()
        if not row:
            conn.close()
            return False
        conn.execute("DELETE FROM recipe_images WHERE id = ?", (image_id,))
        conn.commit()
        conn.close()
        return True

    # --- Nutrition Info operations (Feature 14) ---

    def set_nutrition(self, recipe_id: int, calories: int = 0, protein_g: float = 0.0,
                      carbs_g: float = 0.0, fat_g: float = 0.0,
                      fiber_g: float = 0.0, sodium_mg: float = 0.0) -> NutritionInfo:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO nutrition_info (recipe_id, calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(recipe_id) DO UPDATE SET
               calories=?, protein_g=?, carbs_g=?, fat_g=?, fiber_g=?, sodium_mg=?""",
            (recipe_id, calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg,
             calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM nutrition_info WHERE recipe_id = ?", (recipe_id,)).fetchone()
        conn.close()
        return NutritionInfo(**dict(row))

    def get_nutrition(self, recipe_id: int) -> NutritionInfo | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM nutrition_info WHERE recipe_id = ?", (recipe_id,)).fetchone()
        conn.close()
        return NutritionInfo(**dict(row)) if row else None

    # --- Recipe Step operations (Feature 15) ---

    def set_recipe_steps(self, recipe_id: int, steps: list[dict]) -> list[RecipeStep]:
        """Set steps for a recipe (replaces existing). Each step: {title, description, image_url, timer_minutes}"""
        conn = self._get_conn()
        conn.execute("DELETE FROM recipe_steps WHERE recipe_id = ?", (recipe_id,))
        result = []
        for i, step in enumerate(steps, 1):
            cur = conn.execute(
                "INSERT INTO recipe_steps (recipe_id, step_number, title, description, image_url, timer_minutes) VALUES (?, ?, ?, ?, ?, ?)",
                (recipe_id, i, step.get("title", ""), step["description"],
                 step.get("image_url", ""), step.get("timer_minutes", 0)),
            )
            result.append(RecipeStep(
                id=cur.lastrowid, recipe_id=recipe_id, step_number=i,
                title=step.get("title", ""), description=step["description"],
                image_url=step.get("image_url", ""), timer_minutes=step.get("timer_minutes", 0),
            ))
        conn.commit()
        conn.close()
        return result

    def get_recipe_steps(self, recipe_id: int) -> list[RecipeStep]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM recipe_steps WHERE recipe_id = ? ORDER BY step_number",
            (recipe_id,),
        ).fetchall()
        conn.close()
        return [RecipeStep(**dict(r)) for r in rows]

    # --- Ingredient Price operations (Feature 16) ---

    def set_ingredient_price(self, name: str, price: float, unit: str = "") -> IngredientPrice:
        if price < 0:
            raise ValueError("가격은 0 이상이어야 합니다")
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO ingredient_prices (name, price, unit, updated_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET price=?, unit=?, updated_at=?""",
            (name.strip().lower(), price, unit, now, price, unit, now),
        )
        conn.commit()
        conn.close()
        return IngredientPrice(name=name.strip().lower(), price=price, unit=unit, updated_at=now)

    def get_ingredient_price(self, name: str) -> IngredientPrice | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM ingredient_prices WHERE name = ?", (name.strip().lower(),),
        ).fetchone()
        conn.close()
        return IngredientPrice(**dict(row)) if row else None

    def estimate_recipe_cost(self, recipe_id: int) -> dict:
        """Estimate total cost of a recipe based on ingredient prices."""
        ingredients = self.get_recipe_ingredients(recipe_id)
        total = 0.0
        details = []
        for ing in ingredients:
            price_info = self.get_ingredient_price(ing.name)
            cost = price_info.price if price_info else 0.0
            total += cost
            details.append({
                "name": ing.name,
                "price": cost,
                "has_price": price_info is not None,
            })
        return {"total_estimated_cost": round(total, 2), "ingredients": details}

    # --- Badge operations (Feature 17) ---

    def _award_badge(self, user_id: int, badge_code: str) -> bool:
        """Award a badge to user if not already earned. Returns True if newly awarded."""
        conn = self._get_conn()
        badge = conn.execute("SELECT id FROM badges WHERE code = ?", (badge_code,)).fetchone()
        if not badge:
            conn.close()
            return False
        now = time.time()
        try:
            conn.execute(
                "INSERT INTO user_badges (user_id, badge_id, earned_at) VALUES (?, ?, ?)",
                (user_id, badge["id"], now),
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_user_badges(self, user_id: int) -> list[UserBadge]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT ub.*, b.code as badge_code, b.name as badge_name
               FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
               WHERE ub.user_id = ? ORDER BY ub.earned_at DESC""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [UserBadge(**dict(r)) for r in rows]

    def check_and_award_badges(self, user_id: int) -> list[str]:
        """Check all badge conditions and award any earned badges. Returns newly awarded badge codes."""
        awarded = []
        user = self.get_user(user_id)
        if not user:
            return awarded

        # first_recipe: has at least 1 recipe
        recipes = self.get_user_recipes(user_id)
        if len(recipes) >= 1 and self._award_badge(user_id, "first_recipe"):
            awarded.append("first_recipe")
        if len(recipes) >= 10 and self._award_badge(user_id, "recipe_10"):
            awarded.append("recipe_10")

        # liked_50: total likes received >= 50
        total_likes = sum(r.like_count for r in recipes)
        if total_likes >= 50 and self._award_badge(user_id, "liked_50"):
            awarded.append("liked_50")

        # cook_5: at least 5 cook logs
        cook_logs = self.get_user_cook_logs(user_id, limit=5)
        if len(cook_logs) >= 5 and self._award_badge(user_id, "cook_5"):
            awarded.append("cook_5")

        # follower_10
        if self.get_follower_count(user_id) >= 10 and self._award_badge(user_id, "follower_10"):
            awarded.append("follower_10")

        # comment_20
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM comments WHERE user_id = ?", (user_id,),
        ).fetchone()
        conn.close()
        if row["cnt"] >= 20 and self._award_badge(user_id, "comment_20"):
            awarded.append("comment_20")

        # collector
        colls = self.get_user_collections(user_id)
        if len(colls) >= 1 and self._award_badge(user_id, "collector"):
            awarded.append("collector")

        # forker
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM recipes WHERE author_id = ? AND forked_from_id IS NOT NULL",
            (user_id,),
        ).fetchone()
        conn.close()
        if row["cnt"] >= 1 and self._award_badge(user_id, "forker"):
            awarded.append("forker")

        # rating_10
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM ratings WHERE user_id = ?", (user_id,),
        ).fetchone()
        conn.close()
        if row["cnt"] >= 10 and self._award_badge(user_id, "rating_10"):
            awarded.append("rating_10")

        # points_100
        if user.points >= 100 and self._award_badge(user_id, "points_100"):
            awarded.append("points_100")

        return awarded

    def get_all_badges(self) -> list[Badge]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM badges ORDER BY id").fetchall()
        conn.close()
        return [Badge(**dict(r)) for r in rows]

    # --- Recipe Recommendation (Feature 18) ---

    def get_similar_recipes(self, recipe_id: int, limit: int = 10) -> list[Recipe]:
        """Find similar recipes based on shared ingredients and tags."""
        # Get this recipe's ingredients
        ingredients = self.get_recipe_ingredients(recipe_id)
        tags = self.get_recipe_tags(recipe_id)

        if not ingredients and not tags:
            return []

        conn = self._get_conn()

        # Score by shared ingredients
        ing_names = [i.name.lower() for i in ingredients]
        like_conditions = " OR ".join("LOWER(i.name) LIKE ?" for _ in ing_names)
        like_params = [f"%{n}%" for n in ing_names]

        query = f"""
            SELECT r.*, u.username as author_name,
                   COUNT(DISTINCT i.name) as shared_ingredients
            FROM recipes r
            JOIN users u ON r.author_id = u.id
            LEFT JOIN ingredients i ON i.recipe_id = r.id AND ({like_conditions})
            WHERE r.id != ?
            GROUP BY r.id
            HAVING shared_ingredients > 0
            ORDER BY shared_ingredients DESC, r.rating_avg DESC
            LIMIT ?
        """
        rows = conn.execute(query, [*like_params, recipe_id, limit]).fetchall()
        conn.close()

        return [Recipe(**{k: v for k, v in dict(r).items() if k != "shared_ingredients"}) for r in rows]

    # --- Advanced Filter (Feature 19) ---

    def filter_recipes(self, difficulty: str | None = None, max_time: int | None = None,
                       min_rating: float | None = None, tag: str | None = None,
                       sort_by: str = "recent", offset: int = 0, limit: int = 20) -> list[Recipe]:
        """Advanced recipe filtering with multiple criteria."""
        conditions = []
        params: list = []

        if difficulty:
            conditions.append("r.difficulty = ?")
            params.append(difficulty)
        if max_time is not None:
            conditions.append("r.cooking_time_min <= ?")
            params.append(max_time)
        if min_rating is not None:
            conditions.append("r.rating_avg >= ?")
            params.append(min_rating)

        join_tag = ""
        if tag:
            join_tag = "JOIN recipe_tags rt ON rt.recipe_id = r.id JOIN tags t ON rt.tag_id = t.id"
            conditions.append("t.name = ?")
            params.append(tag.strip().lower())

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        order_map = {
            "recent": "r.created_at DESC",
            "popular": "r.like_count DESC, r.created_at DESC",
            "rating": "r.rating_avg DESC, r.rating_count DESC",
            "cooking_time": "r.cooking_time_min ASC",
            "most_cooked": "r.cook_count DESC",
            "most_forked": "r.fork_count DESC",
        }
        order = order_map.get(sort_by, "r.created_at DESC")

        conn = self._get_conn()
        rows = conn.execute(
            f"""SELECT DISTINCT r.*, u.username as author_name
                FROM recipes r
                JOIN users u ON r.author_id = u.id
                {join_tag}
                {where}
                ORDER BY {order} LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Cooking Timer operations (Feature 20) ---

    def set_cooking_timers(self, recipe_id: int, timers: list[dict]) -> list[CookingTimer]:
        """Set timer presets for a recipe (replaces existing).
        Each timer: {label, duration_seconds}"""
        conn = self._get_conn()
        conn.execute("DELETE FROM cooking_timers WHERE recipe_id = ?", (recipe_id,))
        result = []
        for i, t in enumerate(timers):
            if not t.get("label") or not t.get("duration_seconds"):
                continue
            cur = conn.execute(
                "INSERT INTO cooking_timers (recipe_id, label, duration_seconds, sort_order) VALUES (?, ?, ?, ?)",
                (recipe_id, t["label"], t["duration_seconds"], i),
            )
            result.append(CookingTimer(
                id=cur.lastrowid, recipe_id=recipe_id,
                label=t["label"], duration_seconds=t["duration_seconds"], sort_order=i,
            ))
        conn.commit()
        conn.close()
        return result

    def get_cooking_timers(self, recipe_id: int) -> list[CookingTimer]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM cooking_timers WHERE recipe_id = ? ORDER BY sort_order",
            (recipe_id,),
        ).fetchall()
        conn.close()
        return [CookingTimer(**dict(r)) for r in rows]

    # --- Meal Plan operations (Feature 21) ---

    def set_meal_plan(self, user_id: int, date: str, meal_type: str, recipe_id: int, note: str = "") -> MealPlan:
        if meal_type not in ("breakfast", "lunch", "dinner", "snack"):
            raise ValueError("잘못된 식사 유형입니다")
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO meal_plans (user_id, date, meal_type, recipe_id, note)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id, date, meal_type) DO UPDATE SET recipe_id=?, note=?""",
            (user_id, date, meal_type, recipe_id, note, recipe_id, note),
        )
        conn.commit()
        conn.close()
        return MealPlan(user_id=user_id, date=date, meal_type=meal_type, recipe_id=recipe_id, note=note)

    def get_meal_plans(self, user_id: int, start_date: str, end_date: str) -> list[MealPlan]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM meal_plans WHERE user_id = ? AND date >= ? AND date <= ? ORDER BY date, meal_type",
            (user_id, start_date, end_date),
        ).fetchall()
        conn.close()
        return [MealPlan(**dict(r)) for r in rows]

    def delete_meal_plan(self, user_id: int, date: str, meal_type: str) -> bool:
        conn = self._get_conn()
        result = conn.execute(
            "DELETE FROM meal_plans WHERE user_id = ? AND date = ? AND meal_type = ?",
            (user_id, date, meal_type),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    # --- Shopping List operations (Feature 22) ---

    def add_shopping_item(self, user_id: int, name: str, amount: str = "", unit: str = "", recipe_id: int | None = None) -> ShoppingItem:
        if not name.strip():
            raise ValueError("재료명을 입력하세요")
        conn = self._get_conn()
        cur = conn.execute(
            "INSERT INTO shopping_items (user_id, name, amount, unit, recipe_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, name.strip(), amount, unit, recipe_id),
        )
        conn.commit()
        item_id = cur.lastrowid
        conn.close()
        return ShoppingItem(id=item_id, user_id=user_id, name=name.strip(), amount=amount, unit=unit, recipe_id=recipe_id)

    def add_recipe_to_shopping(self, user_id: int, recipe_id: int) -> list[ShoppingItem]:
        """Add all ingredients of a recipe to shopping list."""
        ingredients = self.get_recipe_ingredients(recipe_id)
        if not ingredients:
            raise ValueError("레시피에 재료가 없습니다")
        items = []
        for ing in ingredients:
            items.append(self.add_shopping_item(user_id, ing.name, ing.amount, ing.unit, recipe_id))
        return items

    def get_shopping_list(self, user_id: int) -> list[ShoppingItem]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM shopping_items WHERE user_id = ? ORDER BY checked, id",
            (user_id,),
        ).fetchall()
        conn.close()
        return [ShoppingItem(**dict(r)) for r in rows]

    def toggle_shopping_item(self, item_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        result = conn.execute(
            "UPDATE shopping_items SET checked = NOT checked WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def delete_shopping_item(self, item_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        result = conn.execute(
            "DELETE FROM shopping_items WHERE id = ? AND user_id = ?", (item_id, user_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def clear_shopping_list(self, user_id: int, checked_only: bool = False) -> int:
        conn = self._get_conn()
        if checked_only:
            result = conn.execute("DELETE FROM shopping_items WHERE user_id = ? AND checked = 1", (user_id,))
        else:
            result = conn.execute("DELETE FROM shopping_items WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return result.rowcount

    # --- Block User operations (Feature 23) ---

    def block_user(self, blocker_id: int, blocked_id: int) -> dict:
        if blocker_id == blocked_id:
            raise ValueError("자기 자신을 차단할 수 없습니다")
        conn = self._get_conn()
        try:
            now = time.time()
            conn.execute(
                "INSERT INTO blocked_users (blocker_id, blocked_id, created_at) VALUES (?, ?, ?)",
                (blocker_id, blocked_id, now),
            )
            # Also unfollow if following
            conn.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (blocker_id, blocked_id))
            conn.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (blocked_id, blocker_id))
            conn.commit()
            conn.close()
            return {"blocked": True}
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 차단된 유저입니다")

    def unblock_user(self, blocker_id: int, blocked_id: int) -> bool:
        conn = self._get_conn()
        result = conn.execute(
            "DELETE FROM blocked_users WHERE blocker_id = ? AND blocked_id = ?",
            (blocker_id, blocked_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def is_blocked(self, blocker_id: int, blocked_id: int) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id FROM blocked_users WHERE blocker_id = ? AND blocked_id = ?",
            (blocker_id, blocked_id),
        ).fetchone()
        conn.close()
        return row is not None

    def get_blocked_users(self, user_id: int) -> list[User]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT u.* FROM blocked_users bu
               JOIN users u ON bu.blocked_id = u.id
               WHERE bu.blocker_id = ?""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [User(**dict(r)) for r in rows]

    # --- Recipe Q&A operations (Feature 24) ---

    def ask_question(self, recipe_id: int, user_id: int, question: str) -> QA:
        question = question.strip()
        if not question:
            raise ValueError("질문을 입력하세요")
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO recipe_qa (recipe_id, user_id, question, created_at) VALUES (?, ?, ?, ?)",
            (recipe_id, user_id, question, now),
        )
        conn.commit()
        qa_id = cur.lastrowid
        conn.close()
        return QA(id=qa_id, recipe_id=recipe_id, user_id=user_id, question=question, created_at=now)

    def answer_question(self, qa_id: int, user_id: int, answer: str) -> QA | None:
        answer = answer.strip()
        if not answer:
            raise ValueError("답변을 입력하세요")
        conn = self._get_conn()
        now = time.time()
        result = conn.execute(
            "UPDATE recipe_qa SET answer = ?, answered_by = ?, answered_at = ? WHERE id = ?",
            (answer, user_id, now, qa_id),
        )
        if result.rowcount == 0:
            conn.close()
            return None
        row = conn.execute(
            "SELECT qa.*, u.username FROM recipe_qa qa JOIN users u ON qa.user_id = u.id WHERE qa.id = ?",
            (qa_id,),
        ).fetchone()
        conn.commit()
        conn.close()
        self.update_points(user_id, POINTS_QA_ANSWER, "Q&A 답변")
        return QA(**dict(row)) if row else None

    def get_recipe_qa(self, recipe_id: int) -> list[QA]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT qa.*, u.username FROM recipe_qa qa JOIN users u ON qa.user_id = u.id WHERE qa.recipe_id = ? ORDER BY qa.created_at DESC",
            (recipe_id,),
        ).fetchall()
        conn.close()
        return [QA(**dict(r)) for r in rows]

    # --- Season Recipe operations (Feature 25) ---

    def set_recipe_season(self, recipe_id: int, season: str) -> bool:
        valid = ("spring", "summer", "fall", "winter", "all", "")
        if season not in valid:
            raise ValueError("잘못된 계절입니다")
        conn = self._get_conn()
        result = conn.execute("UPDATE recipes SET season = ? WHERE id = ?", (season, recipe_id))
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def get_seasonal_recipes(self, season: str, limit: int = 50) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name FROM recipes r
               JOIN users u ON r.author_id = u.id
               WHERE r.season = ? OR r.season = 'all'
               ORDER BY r.rating_avg DESC LIMIT ?""",
            (season, limit),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Allergy Info operations (Feature 26) ---

    COMMON_ALLERGENS = ["gluten", "dairy", "eggs", "nuts", "peanuts", "soy", "shellfish", "fish", "wheat", "sesame"]

    def set_allergens(self, recipe_id: int, allergens: list[str]) -> list[str]:
        conn = self._get_conn()
        conn.execute("DELETE FROM allergy_info WHERE recipe_id = ?", (recipe_id,))
        result = []
        for a in allergens:
            a = a.strip().lower()
            if a:
                conn.execute("INSERT OR IGNORE INTO allergy_info (recipe_id, allergen) VALUES (?, ?)", (recipe_id, a))
                result.append(a)
        conn.commit()
        conn.close()
        return result

    def get_allergens(self, recipe_id: int) -> list[str]:
        conn = self._get_conn()
        rows = conn.execute("SELECT allergen FROM allergy_info WHERE recipe_id = ?", (recipe_id,)).fetchall()
        conn.close()
        return [r["allergen"] for r in rows]

    def find_recipes_without_allergens(self, exclude_allergens: list[str], limit: int = 50) -> list[Recipe]:
        """Find recipes that do NOT contain any of the specified allergens."""
        if not exclude_allergens:
            return self.list_recipes(limit=limit)
        conn = self._get_conn()
        placeholders = ",".join("?" for _ in exclude_allergens)
        rows = conn.execute(
            f"""SELECT r.*, u.username as author_name FROM recipes r
                JOIN users u ON r.author_id = u.id
                WHERE r.id NOT IN (
                    SELECT recipe_id FROM allergy_info WHERE allergen IN ({placeholders})
                )
                ORDER BY r.rating_avg DESC LIMIT ?""",
            (*[a.lower() for a in exclude_allergens], limit),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Difficulty Vote operations (Feature 27) ---

    def vote_difficulty(self, recipe_id: int, user_id: int, vote: str) -> dict:
        if vote not in ("easy", "medium", "hard"):
            raise ValueError("잘못된 난이도입니다")
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO difficulty_votes (recipe_id, user_id, vote, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, recipe_id) DO UPDATE SET vote=?, created_at=?""",
            (recipe_id, user_id, vote, now, vote, now),
        )
        conn.commit()
        # Get distribution
        rows = conn.execute(
            "SELECT vote, COUNT(*) as cnt FROM difficulty_votes WHERE recipe_id = ? GROUP BY vote",
            (recipe_id,),
        ).fetchall()
        conn.close()
        dist = {"easy": 0, "medium": 0, "hard": 0}
        for r in rows:
            dist[r["vote"]] = r["cnt"]
        total = sum(dist.values())
        return {"distribution": dist, "total_votes": total, "your_vote": vote}

    def get_difficulty_votes(self, recipe_id: int) -> dict:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT vote, COUNT(*) as cnt FROM difficulty_votes WHERE recipe_id = ? GROUP BY vote",
            (recipe_id,),
        ).fetchall()
        conn.close()
        dist = {"easy": 0, "medium": 0, "hard": 0}
        for r in rows:
            dist[r["vote"]] = r["cnt"]
        return {"distribution": dist, "total_votes": sum(dist.values())}

    # --- Recipe Compare (Feature 28) ---

    def compare_recipes(self, recipe_id_a: int, recipe_id_b: int) -> dict:
        a = self.get_recipe(recipe_id_a)
        b = self.get_recipe(recipe_id_b)
        if not a or not b:
            raise ValueError("레시피를 찾을 수 없습니다")
        ing_a = {i.name.lower() for i in self.get_recipe_ingredients(recipe_id_a)}
        ing_b = {i.name.lower() for i in self.get_recipe_ingredients(recipe_id_b)}
        nut_a = self.get_nutrition(recipe_id_a)
        nut_b = self.get_nutrition(recipe_id_b)
        return {
            "recipe_a": {"id": a.id, "title": a.title, "difficulty": a.difficulty,
                         "cooking_time": a.cooking_time_min, "rating": a.rating_avg,
                         "likes": a.like_count, "servings": a.servings},
            "recipe_b": {"id": b.id, "title": b.title, "difficulty": b.difficulty,
                         "cooking_time": b.cooking_time_min, "rating": b.rating_avg,
                         "likes": b.like_count, "servings": b.servings},
            "shared_ingredients": sorted(ing_a & ing_b),
            "only_in_a": sorted(ing_a - ing_b),
            "only_in_b": sorted(ing_b - ing_a),
            "nutrition_a": {"calories": nut_a.calories, "protein": nut_a.protein_g} if nut_a else None,
            "nutrition_b": {"calories": nut_b.calories, "protein": nut_b.protein_g} if nut_b else None,
        }

    # --- User Statistics (Feature 29) ---

    def get_user_stats(self, user_id: int) -> dict:
        conn = self._get_conn()
        recipes = conn.execute("SELECT COUNT(*) as cnt FROM recipes WHERE author_id = ?", (user_id,)).fetchone()["cnt"]
        comments = conn.execute("SELECT COUNT(*) as cnt FROM comments WHERE user_id = ?", (user_id,)).fetchone()["cnt"]
        likes_given = conn.execute("SELECT COUNT(*) as cnt FROM likes WHERE user_id = ?", (user_id,)).fetchone()["cnt"]
        likes_received = conn.execute(
            "SELECT COALESCE(SUM(like_count),0) as cnt FROM recipes WHERE author_id = ?", (user_id,),
        ).fetchone()["cnt"]
        ratings_given = conn.execute("SELECT COUNT(*) as cnt FROM ratings WHERE user_id = ?", (user_id,)).fetchone()["cnt"]
        cook_logs = conn.execute("SELECT COUNT(*) as cnt FROM cook_logs WHERE user_id = ?", (user_id,)).fetchone()["cnt"]
        followers = conn.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (user_id,)).fetchone()["cnt"]
        following = conn.execute("SELECT COUNT(*) as cnt FROM follows WHERE follower_id = ?", (user_id,)).fetchone()["cnt"]
        conn.close()
        user = self.get_user(user_id)
        level_name = "초보 요리사"
        for threshold, name in USER_LEVELS:
            if user and user.points >= threshold:
                level_name = name
        return {
            "recipes": recipes, "comments": comments, "likes_given": likes_given,
            "likes_received": likes_received, "ratings_given": ratings_given,
            "cook_logs": cook_logs, "followers": followers, "following": following,
            "points": user.points if user else 0, "level": level_name,
            "badges": len(self.get_user_badges(user_id)),
        }

    # --- View History operations (Feature 30) ---

    def record_view(self, user_id: int, recipe_id: int) -> None:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            "INSERT INTO view_history (user_id, recipe_id, viewed_at) VALUES (?, ?, ?)",
            (user_id, recipe_id, now),
        )
        conn.execute("UPDATE recipes SET view_count = view_count + 1 WHERE id = ?", (recipe_id,))
        conn.commit()
        conn.close()

    def get_view_history(self, user_id: int, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT DISTINCT vh.recipe_id, MAX(vh.viewed_at) as last_viewed,
                      r.title, r.author_id, u.username as author_name
               FROM view_history vh
               JOIN recipes r ON vh.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE vh.user_id = ?
               GROUP BY vh.recipe_id
               ORDER BY last_viewed DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [{"recipe_id": r["recipe_id"], "title": r["title"],
                 "author_name": r["author_name"], "last_viewed": r["last_viewed"]} for r in rows]

    # --- Ingredient Substitution (Feature 31) ---

    def add_substitution(self, original: str, substitute: str, note: str = "") -> IngredientSub:
        if not original.strip() or not substitute.strip():
            raise ValueError("재료명을 입력하세요")
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO ingredient_subs (original, substitute, note) VALUES (?, ?, ?)",
                (original.strip().lower(), substitute.strip(), note.strip()),
            )
            conn.commit()
            sub_id = cur.lastrowid
            conn.close()
            return IngredientSub(id=sub_id, original=original.strip().lower(),
                                 substitute=substitute.strip(), note=note.strip())
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 등록된 대체 재료입니다")

    def get_substitutions(self, ingredient: str) -> list[IngredientSub]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM ingredient_subs WHERE original = ?", (ingredient.strip().lower(),),
        ).fetchall()
        conn.close()
        return [IngredientSub(**dict(r)) for r in rows]

    # --- Cooking Challenge operations (Feature 32) ---

    def create_challenge(self, title: str, description: str, ingredient: str,
                         start_date: str, end_date: str) -> Challenge:
        if not title.strip():
            raise ValueError("챌린지 제목을 입력하세요")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO challenges (title, description, ingredient, start_date, end_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title.strip(), description.strip(), ingredient.strip(), start_date, end_date, now),
        )
        conn.commit()
        ch_id = cur.lastrowid
        conn.close()
        return Challenge(id=ch_id, title=title.strip(), description=description.strip(),
                         ingredient=ingredient.strip(), start_date=start_date, end_date=end_date, created_at=now)

    def enter_challenge(self, challenge_id: int, user_id: int, recipe_id: int) -> dict:
        conn = self._get_conn()
        now = time.time()
        try:
            conn.execute(
                "INSERT INTO challenge_entries (challenge_id, user_id, recipe_id, created_at) VALUES (?, ?, ?, ?)",
                (challenge_id, user_id, recipe_id, now),
            )
            conn.commit()
            conn.close()
            self.update_points(user_id, POINTS_CHALLENGE_COMPLETE, "챌린지 참여")
            return {"entered": True}
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 참여한 챌린지입니다")

    def get_challenge_entries(self, challenge_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT ce.*, u.username, r.title as recipe_title
               FROM challenge_entries ce
               JOIN users u ON ce.user_id = u.id
               JOIN recipes r ON ce.recipe_id = r.id
               WHERE ce.challenge_id = ?
               ORDER BY ce.created_at""",
            (challenge_id,),
        ).fetchall()
        conn.close()
        return [{"user_id": r["user_id"], "username": r["username"],
                 "recipe_id": r["recipe_id"], "recipe_title": r["recipe_title"]} for r in rows]

    def get_active_challenges(self, date: str = "") -> list[Challenge]:
        if not date:
            date = time.strftime("%Y-%m-%d")
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM challenges WHERE start_date <= ? AND end_date >= ? ORDER BY end_date",
            (date, date),
        ).fetchall()
        conn.close()
        return [Challenge(**dict(r)) for r in rows]

    # --- Poll operations (Feature 33) ---

    def create_poll(self, recipe_id: int, user_id: int, question: str, options: list[str]) -> dict:
        if not question.strip() or len(options) < 2:
            raise ValueError("질문과 2개 이상의 선택지를 입력하세요")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO polls (recipe_id, question, created_by, created_at) VALUES (?, ?, ?, ?)",
            (recipe_id, question.strip(), user_id, now),
        )
        poll_id = cur.lastrowid
        opt_list = []
        for text in options:
            if text.strip():
                c = conn.execute(
                    "INSERT INTO poll_options (poll_id, text) VALUES (?, ?)", (poll_id, text.strip()),
                )
                opt_list.append({"id": c.lastrowid, "text": text.strip(), "vote_count": 0})
        conn.commit()
        conn.close()
        return {"poll_id": poll_id, "question": question.strip(), "options": opt_list}

    def vote_poll(self, poll_id: int, option_id: int, user_id: int) -> dict:
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO poll_votes (poll_id, option_id, user_id) VALUES (?, ?, ?)",
                (poll_id, option_id, user_id),
            )
            conn.execute("UPDATE poll_options SET vote_count = vote_count + 1 WHERE id = ?", (option_id,))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 투표했습니다")
        rows = conn.execute(
            "SELECT * FROM poll_options WHERE poll_id = ? ORDER BY id", (poll_id,),
        ).fetchall()
        conn.close()
        return {"options": [{"id": r["id"], "text": r["text"], "vote_count": r["vote_count"]} for r in rows]}

    def get_poll(self, poll_id: int) -> dict | None:
        conn = self._get_conn()
        poll = conn.execute("SELECT * FROM polls WHERE id = ?", (poll_id,)).fetchone()
        if not poll:
            conn.close()
            return None
        options = conn.execute("SELECT * FROM poll_options WHERE poll_id = ? ORDER BY id", (poll_id,)).fetchall()
        conn.close()
        return {
            "id": poll["id"], "question": poll["question"], "recipe_id": poll["recipe_id"],
            "options": [{"id": o["id"], "text": o["text"], "vote_count": o["vote_count"]} for o in options],
        }

    # --- User Level (Feature 34) ---

    def get_user_level(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise ValueError("유저를 찾을 수 없습니다")
        level_name = USER_LEVELS[0][1]
        current_threshold = 0
        next_threshold = USER_LEVELS[1][0] if len(USER_LEVELS) > 1 else None
        for i, (threshold, name) in enumerate(USER_LEVELS):
            if user.points >= threshold:
                level_name = name
                current_threshold = threshold
                next_threshold = USER_LEVELS[i + 1][0] if i + 1 < len(USER_LEVELS) else None
        return {
            "level": level_name,
            "points": user.points,
            "current_threshold": current_threshold,
            "next_threshold": next_threshold,
            "points_to_next": (next_threshold - user.points) if next_threshold else 0,
        }

    # --- Recipe Tips (Feature 35) ---

    def add_recipe_tip(self, recipe_id: int, user_id: int, content: str) -> RecipeTip:
        content = content.strip()
        if not content:
            raise ValueError("팁 내용을 입력하세요")
        if len(content) > 1000:
            raise ValueError("팁은 1000자 이하로 작성하세요")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO recipe_tips (recipe_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
            (recipe_id, user_id, content, now),
        )
        conn.commit()
        tip_id = cur.lastrowid
        conn.close()
        return RecipeTip(id=tip_id, recipe_id=recipe_id, user_id=user_id, content=content, created_at=now)

    def get_recipe_tips(self, recipe_id: int) -> list[RecipeTip]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT rt.*, u.username FROM recipe_tips rt JOIN users u ON rt.user_id = u.id WHERE rt.recipe_id = ? ORDER BY rt.created_at DESC",
            (recipe_id,),
        ).fetchall()
        conn.close()
        return [RecipeTip(**dict(r)) for r in rows]

    # --- Recipe Export (Feature 36) ---

    def export_recipe(self, recipe_id: int, format: str = "json") -> dict | str:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        ingredients = self.get_recipe_ingredients(recipe_id)
        steps = self.get_recipe_steps(recipe_id)
        nutrition = self.get_nutrition(recipe_id)
        tags = self.get_recipe_tags(recipe_id)

        data = {
            "title": recipe.title,
            "description": recipe.description,
            "author": recipe.author_name,
            "difficulty": recipe.difficulty,
            "cooking_time_min": recipe.cooking_time_min,
            "servings": recipe.servings,
            "ingredients": [{"name": i.name, "amount": i.amount, "unit": i.unit} for i in ingredients],
            "steps": [{"step": s.step_number, "title": s.title, "description": s.description} for s in steps],
            "instructions": recipe.instructions,
            "tags": tags,
            "nutrition": {
                "calories": nutrition.calories, "protein_g": nutrition.protein_g,
                "carbs_g": nutrition.carbs_g, "fat_g": nutrition.fat_g,
            } if nutrition else None,
        }

        if format == "text":
            lines = [f"# {recipe.title}", f"작성자: {recipe.author_name}",
                     f"난이도: {recipe.difficulty} | 조리시간: {recipe.cooking_time_min}분 | {recipe.servings}인분", ""]
            lines.append("## 재료")
            for i in ingredients:
                lines.append(f"- {i.name} {i.amount} {i.unit}".strip())
            lines.append("")
            if steps:
                lines.append("## 조리 순서")
                for s in steps:
                    title_part = f" ({s.title})" if s.title else ""
                    lines.append(f"{s.step_number}. {s.description}{title_part}")
            else:
                lines.append("## 조리법")
                lines.append(recipe.instructions)
            return "\n".join(lines)

        return data

    # --- Recipe Version operations (Feature 37) ---

    def save_recipe_version(self, recipe_id: int) -> RecipeVersion:
        """Save current state of recipe as a version snapshot."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COALESCE(MAX(version_num), 0) + 1 as next_ver FROM recipe_versions WHERE recipe_id = ?",
            (recipe_id,),
        ).fetchone()
        ver_num = row["next_ver"]
        now = time.time()
        cur = conn.execute(
            "INSERT INTO recipe_versions (recipe_id, version_num, title, description, instructions, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (recipe_id, ver_num, recipe.title, recipe.description, recipe.instructions, now),
        )
        conn.commit()
        ver_id = cur.lastrowid
        conn.close()
        return RecipeVersion(id=ver_id, recipe_id=recipe_id, version_num=ver_num,
                             title=recipe.title, description=recipe.description,
                             instructions=recipe.instructions, created_at=now)

    def get_recipe_versions(self, recipe_id: int) -> list[RecipeVersion]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM recipe_versions WHERE recipe_id = ? ORDER BY version_num DESC",
            (recipe_id,),
        ).fetchall()
        conn.close()
        return [RecipeVersion(**dict(r)) for r in rows]

    # --- Bookmark Tags (Feature 38) ---

    def create_bookmark_tag(self, user_id: int, name: str) -> BookmarkTag:
        if not name.strip():
            raise ValueError("태그 이름을 입력하세요")
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO bookmark_tags (user_id, name) VALUES (?, ?)", (user_id, name.strip()),
            )
            conn.commit()
            tag_id = cur.lastrowid
            conn.close()
            return BookmarkTag(id=tag_id, user_id=user_id, name=name.strip())
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 존재하는 태그입니다")

    def get_bookmark_tags(self, user_id: int) -> list[BookmarkTag]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM bookmark_tags WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [BookmarkTag(**dict(r)) for r in rows]

    def tag_bookmark(self, user_id: int, recipe_id: int, tag_id: int) -> bool:
        conn = self._get_conn()
        bm = conn.execute(
            "SELECT id FROM bookmarks WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id),
        ).fetchone()
        if not bm:
            conn.close()
            raise ValueError("북마크를 찾을 수 없습니다")
        try:
            conn.execute("INSERT INTO bookmark_tag_map (bookmark_id, tag_id) VALUES (?, ?)", (bm["id"], tag_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_bookmarks_by_tag(self, user_id: int, tag_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name
               FROM bookmark_tag_map btm
               JOIN bookmarks b ON btm.bookmark_id = b.id
               JOIN recipes r ON b.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE b.user_id = ? AND btm.tag_id = ?""",
            (user_id, tag_id),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Print Format (Feature 39) ---

    def get_print_format(self, recipe_id: int) -> dict | None:
        """Get recipe in a print-friendly format."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
        ingredients = self.get_recipe_ingredients(recipe_id)
        steps = self.get_recipe_steps(recipe_id)
        nutrition = self.get_nutrition(recipe_id)
        timers = self.get_cooking_timers(recipe_id)
        return {
            "title": recipe.title,
            "author": recipe.author_name,
            "difficulty": recipe.difficulty,
            "cooking_time_min": recipe.cooking_time_min,
            "servings": recipe.servings,
            "description": recipe.description,
            "ingredients": [f"{i.name} {i.amount} {i.unit}".strip() for i in ingredients],
            "steps": [{"num": s.step_number, "text": s.description,
                        "timer": f"{s.timer_minutes}분" if s.timer_minutes else None} for s in steps],
            "instructions": recipe.instructions if not steps else None,
            "nutrition_summary": f"{nutrition.calories}kcal | 단백질 {nutrition.protein_g}g | 탄수화물 {nutrition.carbs_g}g | 지방 {nutrition.fat_g}g" if nutrition else None,
            "timers": [f"{t.label}: {t.duration_seconds // 60}분 {t.duration_seconds % 60}초" for t in timers],
        }

    # --- Duplicate Detection (Feature 40) ---

    def find_duplicates(self, recipe_id: int, threshold: float = 0.7) -> list[dict]:
        """Find potentially duplicate recipes based on title similarity and ingredient overlap."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return []
        my_ings = {i.name.lower() for i in self.get_recipe_ingredients(recipe_id)}
        if not my_ings:
            return []

        conn = self._get_conn()
        # Get all other recipes
        rows = conn.execute(
            """SELECT r.id, r.title, r.author_id, u.username as author_name
               FROM recipes r JOIN users u ON r.author_id = u.id
               WHERE r.id != ?""",
            (recipe_id,),
        ).fetchall()
        conn.close()

        duplicates = []
        for row in rows:
            other_ings = {i.name.lower() for i in self.get_recipe_ingredients(row["id"])}
            if not other_ings:
                continue
            # Jaccard similarity
            intersection = len(my_ings & other_ings)
            union = len(my_ings | other_ings)
            similarity = intersection / union if union else 0

            # Title similarity bonus
            title_a = recipe.title.lower()
            title_b = row["title"].lower()
            title_overlap = len(set(title_a) & set(title_b)) / max(len(set(title_a) | set(title_b)), 1)
            combined = similarity * 0.7 + title_overlap * 0.3

            if combined >= threshold:
                duplicates.append({
                    "recipe_id": row["id"],
                    "title": row["title"],
                    "author_name": row["author_name"],
                    "similarity": round(combined, 2),
                    "shared_ingredients": sorted(my_ings & other_ings),
                })

        duplicates.sort(key=lambda x: x["similarity"], reverse=True)
        return duplicates

    # --- Recipe Category (Feature 41) ---

    def set_recipe_category(self, recipe_id: int, category: str) -> bool:
        if category and category not in RECIPE_CATEGORIES:
            raise ValueError(f"잘못된 카테고리입니다. 사용 가능: {', '.join(RECIPE_CATEGORIES)}")
        conn = self._get_conn()
        result = conn.execute("UPDATE recipes SET category = ? WHERE id = ?", (category, recipe_id))
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def get_recipes_by_category(self, category: str, limit: int = 50) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name FROM recipes r
               JOIN users u ON r.author_id = u.id
               WHERE r.category = ? AND r.is_public = 1
               ORDER BY r.created_at DESC LIMIT ?""",
            (category, limit),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Equipment (Feature 42) ---

    def set_equipment(self, recipe_id: int, equipment: list[str]) -> list[str]:
        conn = self._get_conn()
        conn.execute("DELETE FROM equipment WHERE recipe_id = ?", (recipe_id,))
        result = []
        for name in equipment:
            name = name.strip()
            if name:
                conn.execute("INSERT INTO equipment (recipe_id, name) VALUES (?, ?)", (recipe_id, name))
                result.append(name)
        conn.commit()
        conn.close()
        return result

    def get_equipment(self, recipe_id: int) -> list[str]:
        conn = self._get_conn()
        rows = conn.execute("SELECT name FROM equipment WHERE recipe_id = ?", (recipe_id,)).fetchall()
        conn.close()
        return [r["name"] for r in rows]

    # --- Auto Difficulty (Feature 43) ---

    def calculate_difficulty(self, recipe_id: int) -> str:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        ingredients = self.get_recipe_ingredients(recipe_id)
        steps = self.get_recipe_steps(recipe_id)
        score = 0
        score += min(len(ingredients) * 0.5, 3)
        score += min(recipe.cooking_time_min * 0.02, 3)
        score += min(len(steps) * 0.3, 2)
        if score <= 2:
            return "easy"
        elif score <= 4.5:
            return "medium"
        return "hard"

    # --- Bookmark Sort (Feature 44) ---

    def get_user_bookmarks_sorted(self, user_id: int, sort_by: str = "recent") -> list[Recipe]:
        order_map = {
            "recent": "b.created_at DESC",
            "title": "r.title ASC",
            "rating": "r.rating_avg DESC",
            "popular": "r.like_count DESC",
        }
        order = order_map.get(sort_by, "b.created_at DESC")
        conn = self._get_conn()
        rows = conn.execute(
            f"""SELECT r.*, u.username as author_name FROM bookmarks b
                JOIN recipes r ON b.recipe_id = r.id
                JOIN users u ON r.author_id = u.id
                WHERE b.user_id = ? ORDER BY {order}""",
            (user_id,),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Clone Recipe (Feature 45) ---

    def clone_recipe(self, recipe_id: int, user_id: int) -> Recipe:
        """Clone own recipe as a new draft."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        if recipe.author_id != user_id:
            raise ValueError("본인 레시피만 복제할 수 있습니다")
        ingredients = self.get_recipe_ingredients(recipe_id)
        ing_list = [{"name": i.name, "amount": i.amount, "unit": i.unit} for i in ingredients]
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            """INSERT INTO recipes (title, description, instructions, author_id,
               cooking_time_min, servings, difficulty, category, season, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"{recipe.title} (복사본)", recipe.description, recipe.instructions,
             user_id, recipe.cooking_time_min, recipe.servings, recipe.difficulty,
             recipe.category, recipe.season, now),
        )
        new_id = cur.lastrowid
        for ing in ing_list:
            conn.execute("INSERT INTO ingredients (recipe_id, name, amount, unit) VALUES (?, ?, ?, ?)",
                         (new_id, ing["name"], ing.get("amount", ""), ing.get("unit", "")))
        conn.commit()
        conn.close()
        return Recipe(id=new_id, title=f"{recipe.title} (복사본)", description=recipe.description,
                      instructions=recipe.instructions, author_id=user_id,
                      cooking_time_min=recipe.cooking_time_min, servings=recipe.servings,
                      difficulty=recipe.difficulty, created_at=now)

    # --- User Notes (Feature 46) ---

    def set_user_note(self, user_id: int, recipe_id: int, content: str) -> UserNote:
        content = content.strip()
        if not content:
            raise ValueError("메모 내용을 입력하세요")
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO user_notes (user_id, recipe_id, content, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, recipe_id) DO UPDATE SET content=?, updated_at=?""",
            (user_id, recipe_id, content, now, content, now),
        )
        conn.commit()
        conn.close()
        return UserNote(user_id=user_id, recipe_id=recipe_id, content=content, updated_at=now)

    def get_user_note(self, user_id: int, recipe_id: int) -> UserNote | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM user_notes WHERE user_id = ? AND recipe_id = ?",
                           (user_id, recipe_id)).fetchone()
        conn.close()
        return UserNote(**dict(row)) if row else None

    # --- Unit Converter (Feature 47) ---

    @staticmethod
    def convert_unit(value: float, from_unit: str, to_unit: str) -> float | None:
        key = (from_unit.lower(), to_unit.lower())
        factor = UNIT_CONVERSIONS.get(key)
        if factor is None:
            return None
        return round(value * factor, 4)

    # --- Serving Scaler (Feature 48) ---

    def scale_recipe(self, recipe_id: int, target_servings: int) -> dict:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        if target_servings < 1:
            raise ValueError("1인분 이상이어야 합니다")
        ingredients = self.get_recipe_ingredients(recipe_id)
        ratio = target_servings / max(recipe.servings, 1)
        scaled = []
        for ing in ingredients:
            try:
                amount = float(ing.amount) * ratio if ing.amount else ""
                amount_str = str(round(amount, 2)) if isinstance(amount, float) else ""
            except (ValueError, TypeError):
                amount_str = ing.amount
            scaled.append({"name": ing.name, "amount": amount_str, "unit": ing.unit})
        return {"original_servings": recipe.servings, "target_servings": target_servings,
                "ratio": round(ratio, 2), "ingredients": scaled}

    # --- Visibility (Feature 49) ---

    def set_recipe_visibility(self, recipe_id: int, user_id: int, is_public: bool) -> bool:
        conn = self._get_conn()
        result = conn.execute("UPDATE recipes SET is_public = ? WHERE id = ? AND author_id = ?",
                              (1 if is_public else 0, recipe_id, user_id))
        conn.commit()
        conn.close()
        return result.rowcount > 0

    # --- Search History (Feature 50) ---

    def record_search(self, user_id: int, query: str) -> None:
        query = query.strip()
        if not query:
            return
        conn = self._get_conn()
        now = time.time()
        conn.execute("INSERT INTO search_history (user_id, query, searched_at) VALUES (?, ?, ?)",
                     (user_id, query, now))
        # Update popular searches
        conn.execute(
            """INSERT INTO popular_searches (query, search_count) VALUES (?, 1)
               ON CONFLICT(query) DO UPDATE SET search_count = search_count + 1""",
            (query.lower(),),
        )
        conn.commit()
        conn.close()

    def get_search_history(self, user_id: int, limit: int = 20) -> list[str]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT DISTINCT query FROM search_history WHERE user_id = ?
               ORDER BY searched_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [r["query"] for r in rows]

    def clear_search_history(self, user_id: int) -> int:
        conn = self._get_conn()
        result = conn.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return result.rowcount

    # --- Ingredient Autocomplete (Feature 51) ---

    def autocomplete_ingredient(self, prefix: str, limit: int = 10) -> list[str]:
        if not prefix.strip():
            return []
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT name, COUNT(*) as cnt FROM ingredients
               WHERE name LIKE ? GROUP BY name ORDER BY cnt DESC LIMIT ?""",
            (f"{prefix.strip()}%", limit),
        ).fetchall()
        conn.close()
        return [r["name"] for r in rows]

    # --- Scheduled Publish (Feature 52) ---

    def schedule_recipe(self, recipe_id: int, user_id: int, publish_at: float) -> bool:
        conn = self._get_conn()
        result = conn.execute(
            "UPDATE recipes SET scheduled_at = ?, is_public = 0 WHERE id = ? AND author_id = ?",
            (publish_at, recipe_id, user_id),
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def publish_scheduled_recipes(self) -> int:
        now = time.time()
        conn = self._get_conn()
        result = conn.execute(
            "UPDATE recipes SET is_public = 1, scheduled_at = NULL WHERE scheduled_at IS NOT NULL AND scheduled_at <= ?",
            (now,),
        )
        conn.commit()
        conn.close()
        return result.rowcount

    # --- Activity Log (Feature 53) ---

    def log_activity(self, user_id: int, action: str, detail: str = "") -> None:
        conn = self._get_conn()
        now = time.time()
        conn.execute("INSERT INTO activity_log (user_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                     (user_id, action, detail, now))
        conn.commit()
        conn.close()

    def get_activity_log(self, user_id: int, limit: int = 50) -> list[ActivityLog]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM activity_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [ActivityLog(**dict(r)) for r in rows]

    # --- Freshness Score (Feature 54) ---

    def get_freshness_score(self, recipe_id: int) -> dict:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError("레시피를 찾을 수 없습니다")
        now = time.time()
        age_days = (now - recipe.created_at) / 86400
        conn = self._get_conn()
        recent_likes = conn.execute(
            "SELECT COUNT(*) as cnt FROM likes WHERE recipe_id = ? AND created_at >= ?",
            (recipe_id, now - 7 * 86400),
        ).fetchone()["cnt"]
        recent_comments = conn.execute(
            "SELECT COUNT(*) as cnt FROM comments WHERE recipe_id = ? AND created_at >= ?",
            (recipe_id, now - 7 * 86400),
        ).fetchone()["cnt"]
        conn.close()
        activity = recent_likes + recent_comments
        # Decay + activity boost
        score = max(0, 100 - age_days * 2) + activity * 5
        return {"score": round(min(score, 100), 1), "age_days": round(age_days, 1),
                "recent_activity": activity}

    # --- Followers Only (Feature 55) ---

    def get_followers_only_recipes(self, viewer_id: int, author_id: int) -> list[Recipe]:
        """Get private recipes only if viewer follows author."""
        if not self.is_following(viewer_id, author_id) and viewer_id != author_id:
            return []
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name FROM recipes r
               JOIN users u ON r.author_id = u.id
               WHERE r.author_id = ? AND r.is_public = 0 ORDER BY r.created_at DESC""",
            (author_id,),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Curated Lists (Feature 56) ---

    def create_curated_list(self, user_id: int, title: str, description: str = "") -> CuratedList:
        if not title.strip():
            raise ValueError("목록 제목을 입력하세요")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO curated_lists (title, description, created_by, created_at) VALUES (?, ?, ?, ?)",
            (title.strip(), description.strip(), user_id, now),
        )
        conn.commit()
        lid = cur.lastrowid
        conn.close()
        return CuratedList(id=lid, title=title.strip(), description=description.strip(),
                           created_by=user_id, created_at=now)

    def add_to_curated_list(self, list_id: int, recipe_id: int, sort_order: int = 0) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO curated_list_items (list_id, recipe_id, sort_order) VALUES (?, ?, ?)",
                         (list_id, recipe_id, sort_order))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_curated_list_recipes(self, list_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username as author_name FROM curated_list_items cli
               JOIN recipes r ON cli.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE cli.list_id = ? ORDER BY cli.sort_order""",
            (list_id,),
        ).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_all_curated_lists(self) -> list[CuratedList]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM curated_lists ORDER BY created_at DESC").fetchall()
        conn.close()
        return [CuratedList(**dict(r)) for r in rows]

    # --- Like Timeline (Feature 57) ---

    def get_like_timeline(self, user_id: int, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT l.created_at, r.id as recipe_id, r.title, u.username as author_name
               FROM likes l JOIN recipes r ON l.recipe_id = r.id
               JOIN users u ON r.author_id = u.id
               WHERE l.user_id = ? ORDER BY l.created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Ingredient Nutrition DB (Feature 58) ---

    def set_ingredient_nutrition(self, name: str, calories: float = 0, protein: float = 0,
                                  carbs: float = 0, fat: float = 0) -> IngredientNutrition:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO ingredient_nutrition (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET calories_per_100g=?, protein_per_100g=?, carbs_per_100g=?, fat_per_100g=?""",
            (name.strip().lower(), calories, protein, carbs, fat, calories, protein, carbs, fat),
        )
        conn.commit()
        conn.close()
        return IngredientNutrition(name=name.strip().lower(), calories_per_100g=calories,
                                    protein_per_100g=protein, carbs_per_100g=carbs, fat_per_100g=fat)

    def get_ingredient_nutrition(self, name: str) -> IngredientNutrition | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM ingredient_nutrition WHERE name = ?",
                           (name.strip().lower(),)).fetchone()
        conn.close()
        return IngredientNutrition(**dict(row)) if row else None

    # --- Tag Trending (Feature 59) ---

    def get_trending_tags(self, days: int = 7, limit: int = 10) -> list[dict]:
        cutoff = time.time() - days * 86400
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT t.name, COUNT(*) as cnt FROM recipe_tags rt
               JOIN tags t ON rt.tag_id = t.id
               JOIN recipes r ON rt.recipe_id = r.id
               WHERE r.created_at >= ?
               GROUP BY t.id ORDER BY cnt DESC LIMIT ?""",
            (cutoff, limit),
        ).fetchall()
        conn.close()
        return [{"name": r["name"], "count": r["cnt"]} for r in rows]

    # --- User Preferences (Feature 60) ---

    def set_user_preferences(self, user_id: int, preferred_categories: list[str] | None = None,
                              excluded_allergens: list[str] | None = None,
                              max_cooking_time: int = 0, preferred_difficulty: str = "") -> UserPreference:
        cats = ",".join(preferred_categories) if preferred_categories else ""
        allergens = ",".join(excluded_allergens) if excluded_allergens else ""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO user_preferences (user_id, preferred_categories, excluded_allergens, max_cooking_time, preferred_difficulty)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET preferred_categories=?, excluded_allergens=?, max_cooking_time=?, preferred_difficulty=?""",
            (user_id, cats, allergens, max_cooking_time, preferred_difficulty,
             cats, allergens, max_cooking_time, preferred_difficulty),
        )
        conn.commit()
        conn.close()
        return UserPreference(user_id=user_id, preferred_categories=cats,
                              excluded_allergens=allergens, max_cooking_time=max_cooking_time,
                              preferred_difficulty=preferred_difficulty)

    def get_user_preferences(self, user_id: int) -> UserPreference | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return UserPreference(**dict(row)) if row else None

    def get_personalized_recipes(self, user_id: int, limit: int = 20) -> list[Recipe]:
        """Get recipes matching user preferences."""
        prefs = self.get_user_preferences(user_id)
        if not prefs:
            return self.list_recipes(limit=limit)
        conditions = ["r.is_public = 1"]
        params: list = []
        if prefs.preferred_categories:
            cats = prefs.preferred_categories.split(",")
            placeholders = ",".join("?" for _ in cats)
            conditions.append(f"r.category IN ({placeholders})")
            params.extend(cats)
        if prefs.max_cooking_time > 0:
            conditions.append("r.cooking_time_min <= ?")
            params.append(prefs.max_cooking_time)
        if prefs.preferred_difficulty:
            conditions.append("r.difficulty = ?")
            params.append(prefs.preferred_difficulty)
        where = " AND ".join(conditions)
        conn = self._get_conn()
        rows = conn.execute(
            f"""SELECT r.*, u.username as author_name FROM recipes r
                JOIN users u ON r.author_id = u.id WHERE {where}
                ORDER BY r.rating_avg DESC LIMIT ?""",
            (*params, limit),
        ).fetchall()
        conn.close()
        recipes = [Recipe(**dict(r)) for r in rows]
        # Filter out excluded allergens
        if prefs.excluded_allergens:
            excluded = set(prefs.excluded_allergens.split(","))
            filtered = []
            for r in recipes:
                allergens = set(self.get_allergens(r.id))
                if not allergens & excluded:
                    filtered.append(r)
            return filtered
        return recipes

    # --- Translation (Feature 61) ---

    def set_translation(self, recipe_id: int, language: str, title: str, description: str = "") -> RecipeTranslation:
        if not title.strip():
            raise ValueError("번역 제목을 입력하세요")
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO recipe_translations (recipe_id, language, title, description)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(recipe_id, language) DO UPDATE SET title=?, description=?""",
            (recipe_id, language, title.strip(), description.strip(), title.strip(), description.strip()),
        )
        conn.commit()
        conn.close()
        return RecipeTranslation(recipe_id=recipe_id, language=language,
                                  title=title.strip(), description=description.strip())

    def get_translations(self, recipe_id: int) -> list[RecipeTranslation]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM recipe_translations WHERE recipe_id = ?", (recipe_id,)).fetchall()
        conn.close()
        return [RecipeTranslation(**dict(r)) for r in rows]

    # --- Cooking Memo (Feature 62) ---
    # Reuses UserNote (Feature 46) — same concept, different name for API clarity

    # --- Pantry (Feature 63) ---

    def add_pantry_item(self, user_id: int, name: str, amount: str = "", unit: str = "", expiry_date: str = "") -> PantryItem:
        if not name.strip():
            raise ValueError("재료명을 입력하세요")
        conn = self._get_conn()
        cur = conn.execute(
            "INSERT INTO pantry (user_id, name, amount, unit, expiry_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, name.strip(), amount, unit, expiry_date),
        )
        conn.commit()
        pid = cur.lastrowid
        conn.close()
        return PantryItem(id=pid, user_id=user_id, name=name.strip(), amount=amount, unit=unit, expiry_date=expiry_date)

    def get_pantry(self, user_id: int) -> list[PantryItem]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM pantry WHERE user_id = ? ORDER BY expiry_date, name", (user_id,)).fetchall()
        conn.close()
        return [PantryItem(**dict(r)) for r in rows]

    def delete_pantry_item(self, item_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        result = conn.execute("DELETE FROM pantry WHERE id = ? AND user_id = ?", (item_id, user_id))
        conn.commit()
        conn.close()
        return result.rowcount > 0

    def find_recipes_from_pantry(self, user_id: int, min_match: float = 0.5) -> list[dict[str, Any]]:
        """Find recipes that can be made with pantry items."""
        pantry = self.get_pantry(user_id)
        if not pantry:
            return []
        names = [p.name for p in pantry]
        return self.find_recipes_by_ingredients(names, min_match_ratio=min_match)

    # --- Social Share Count (Feature 64) ---
    # Reuses ShareLink.view_count — no new table needed, just expose

    def get_share_stats(self, recipe_id: int) -> dict:
        link = self.get_share_link(recipe_id)
        return {"has_share_link": link is not None,
                "view_count": link.view_count if link else 0,
                "token": link.token if link else None}

    # --- Recommendation Reason (Feature 65) ---

    def get_recommendations_with_reasons(self, recipe_id: int, limit: int = 10) -> list[dict]:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return []
        my_ings = {i.name.lower() for i in self.get_recipe_ingredients(recipe_id)}
        my_tags = set(self.get_recipe_tags(recipe_id))
        similar = self.get_similar_recipes(recipe_id, limit=limit)
        results = []
        for r in similar:
            other_ings = {i.name.lower() for i in self.get_recipe_ingredients(r.id)}
            other_tags = set(self.get_recipe_tags(r.id))
            shared_ings = sorted(my_ings & other_ings)
            shared_tags = sorted(my_tags & other_tags)
            reasons = []
            if shared_ings:
                reasons.append(f"공통 재료: {', '.join(shared_ings[:3])}")
            if shared_tags:
                reasons.append(f"공통 태그: {', '.join(shared_tags[:3])}")
            if r.category == recipe.category and r.category:
                reasons.append(f"같은 카테고리: {r.category}")
            results.append({"recipe_id": r.id, "title": r.title, "reasons": reasons})
        return results

    # --- Notification Preferences (Feature 66) ---

    def set_notification_prefs(self, user_id: int, likes: bool = True, comments: bool = True,
                                follows: bool = True, challenges: bool = True) -> NotificationPref:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO notification_prefs (user_id, likes, comments, follows, challenges)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET likes=?, comments=?, follows=?, challenges=?""",
            (user_id, int(likes), int(comments), int(follows), int(challenges),
             int(likes), int(comments), int(follows), int(challenges)),
        )
        conn.commit()
        conn.close()
        return NotificationPref(user_id=user_id, likes=likes, comments=comments,
                                 follows=follows, challenges=challenges)

    def get_notification_prefs(self, user_id: int) -> NotificationPref:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM notification_prefs WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        if not row:
            return NotificationPref(user_id=user_id)
        return NotificationPref(**dict(row))

    # --- Attempt Log (Feature 67) ---

    def log_attempt(self, user_id: int, recipe_id: int, status: str, note: str = "") -> AttemptLog:
        if status not in ("success", "failed", "partial"):
            raise ValueError("잘못된 상태입니다")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO attempt_logs (user_id, recipe_id, status, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, recipe_id, status, note.strip(), now),
        )
        conn.commit()
        aid = cur.lastrowid
        conn.close()
        return AttemptLog(id=aid, user_id=user_id, recipe_id=recipe_id, status=status, note=note.strip(), created_at=now)

    def get_attempt_logs(self, user_id: int, recipe_id: int | None = None, limit: int = 50) -> list[AttemptLog]:
        conn = self._get_conn()
        if recipe_id:
            rows = conn.execute(
                "SELECT * FROM attempt_logs WHERE user_id = ? AND recipe_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, recipe_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM attempt_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        conn.close()
        return [AttemptLog(**dict(r)) for r in rows]

    # --- Popular Searches (Feature 68) ---

    def get_popular_searches(self, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT query, search_count FROM popular_searches ORDER BY search_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [{"query": r["query"], "count": r["search_count"]} for r in rows]

    # --- Recipe Quiz (Feature 69) ---

    def create_quiz(self, recipe_id: int, question: str, correct: str, wrong: list[str]) -> Quiz:
        if not question.strip() or not correct.strip() or len(wrong) < 1:
            raise ValueError("질문, 정답, 오답을 입력하세요")
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO quizzes (recipe_id, question, correct_answer, wrong_answers, created_at) VALUES (?, ?, ?, ?, ?)",
            (recipe_id, question.strip(), correct.strip(), "|".join(w.strip() for w in wrong), now),
        )
        conn.commit()
        qid = cur.lastrowid
        conn.close()
        return Quiz(id=qid, recipe_id=recipe_id, question=question.strip(),
                    correct_answer=correct.strip(), wrong_answers="|".join(w.strip() for w in wrong), created_at=now)

    def get_recipe_quizzes(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM quizzes WHERE recipe_id = ?", (recipe_id,)).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            options = [d["correct_answer"]] + d["wrong_answers"].split("|")
            import random
            random.shuffle(options)
            result.append({"id": d["id"], "question": d["question"], "options": options})
        return result

    def check_quiz_answer(self, quiz_id: int, answer: str) -> dict:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
        conn.close()
        if not row:
            raise ValueError("퀴즈를 찾을 수 없습니다")
        correct = row["correct_answer"] == answer.strip()
        return {"correct": correct, "correct_answer": row["correct_answer"]}

    # --- Health Goals (Feature 70) ---

    def set_health_goal(self, user_id: int, daily_calories: int = 0, daily_protein_g: float = 0,
                         daily_carbs_g: float = 0, daily_fat_g: float = 0) -> HealthGoal:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO health_goals (user_id, daily_calories, daily_protein_g, daily_carbs_g, daily_fat_g)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET daily_calories=?, daily_protein_g=?, daily_carbs_g=?, daily_fat_g=?""",
            (user_id, daily_calories, daily_protein_g, daily_carbs_g, daily_fat_g,
             daily_calories, daily_protein_g, daily_carbs_g, daily_fat_g),
        )
        conn.commit()
        conn.close()
        return HealthGoal(user_id=user_id, daily_calories=daily_calories,
                          daily_protein_g=daily_protein_g, daily_carbs_g=daily_carbs_g, daily_fat_g=daily_fat_g)

    def get_health_goal(self, user_id: int) -> HealthGoal | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM health_goals WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return HealthGoal(**dict(row)) if row else None

    def check_meal_plan_nutrition(self, user_id: int, date: str) -> dict:
        """Check daily nutrition of meal plan vs health goals."""
        plans = self.get_meal_plans(user_id, date, date)
        total_cal, total_pro, total_carb, total_fat = 0, 0.0, 0.0, 0.0
        for p in plans:
            nut = self.get_nutrition(p.recipe_id)
            if nut:
                total_cal += nut.calories
                total_pro += nut.protein_g
                total_carb += nut.carbs_g
                total_fat += nut.fat_g
        goal = self.get_health_goal(user_id)
        return {
            "date": date,
            "consumed": {"calories": total_cal, "protein_g": total_pro, "carbs_g": total_carb, "fat_g": total_fat},
            "goal": {"calories": goal.daily_calories, "protein_g": goal.daily_protein_g,
                     "carbs_g": goal.daily_carbs_g, "fat_g": goal.daily_fat_g} if goal else None,
            "remaining": {
                "calories": goal.daily_calories - total_cal,
                "protein_g": round(goal.daily_protein_g - total_pro, 1),
            } if goal else None,
        }

    # =============================================
    # FEATURES 71-120
    # =============================================

    # --- Rating Reviews (Feature 71) ---

    def add_rating_review(self, rating_id: int, user_id: int, recipe_id: int, text: str) -> RatingReview:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO rating_reviews (rating_id, user_id, recipe_id, text, created_at) VALUES (?,?,?,?,?)",
            (rating_id, user_id, recipe_id, text.strip(), now))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return RatingReview(id=rid, rating_id=rating_id, user_id=user_id, recipe_id=recipe_id, text=text.strip(), created_at=now)

    def get_rating_reviews(self, recipe_id: int, limit: int = 50) -> list[RatingReview]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM rating_reviews WHERE recipe_id=? ORDER BY created_at DESC LIMIT ?",
            (recipe_id, limit)).fetchall()
        conn.close()
        return [RatingReview(**dict(r)) for r in rows]

    # --- Ingredient Groups (Feature 72) ---

    def set_ingredient_groups(self, recipe_id: int, groups: list[dict]) -> list[dict]:
        conn = self._get_conn()
        conn.execute("DELETE FROM ingredient_groups WHERE recipe_id=?", (recipe_id,))
        result = []
        for i, g in enumerate(groups):
            conn.execute("INSERT INTO ingredient_groups (recipe_id, group_name, sort_order) VALUES (?,?,?)",
                         (recipe_id, g["group_name"], g.get("sort_order", i)))
            result.append({"group_name": g["group_name"], "sort_order": g.get("sort_order", i)})
        conn.commit()
        conn.close()
        return result

    def get_ingredient_groups(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT group_name, sort_order FROM ingredient_groups WHERE recipe_id=? ORDER BY sort_order",
            (recipe_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Recipe Drafts (Feature 73) ---

    def save_draft(self, user_id: int, title: str, data_json: str) -> RecipeDraft:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO recipe_drafts (user_id, title, data_json, updated_at) VALUES (?,?,?,?)
               ON CONFLICT(user_id, title) DO UPDATE SET data_json=?, updated_at=?""",
            (user_id, title, data_json, now, data_json, now))
        conn.commit()
        row = conn.execute("SELECT * FROM recipe_drafts WHERE user_id=? AND title=?", (user_id, title)).fetchone()
        conn.close()
        return RecipeDraft(**dict(row))

    def get_drafts(self, user_id: int) -> list[RecipeDraft]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM recipe_drafts WHERE user_id=? ORDER BY updated_at DESC", (user_id,)).fetchall()
        conn.close()
        return [RecipeDraft(**dict(r)) for r in rows]

    def delete_draft(self, draft_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM recipe_drafts WHERE id=? AND user_id=?", (draft_id, user_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # --- Cooking Progress (Feature 74) ---

    def update_cooking_progress(self, user_id: int, recipe_id: int, current_step: int, total_steps: int) -> CookingProgress:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO cooking_progress (user_id, recipe_id, current_step, total_steps, started_at, updated_at)
               VALUES (?,?,?,?,?,?) ON CONFLICT(user_id, recipe_id) DO UPDATE SET current_step=?, total_steps=?, updated_at=?""",
            (user_id, recipe_id, current_step, total_steps, now, now, current_step, total_steps, now))
        conn.commit()
        row = conn.execute("SELECT * FROM cooking_progress WHERE user_id=? AND recipe_id=?", (user_id, recipe_id)).fetchone()
        conn.close()
        return CookingProgress(**dict(row))

    def get_cooking_progress(self, user_id: int, recipe_id: int) -> CookingProgress | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM cooking_progress WHERE user_id=? AND recipe_id=?", (user_id, recipe_id)).fetchone()
        conn.close()
        return CookingProgress(**dict(row)) if row else None

    def clear_cooking_progress(self, user_id: int, recipe_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM cooking_progress WHERE user_id=? AND recipe_id=?", (user_id, recipe_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # --- Recipe Source (Feature 75) ---

    def set_recipe_source(self, recipe_id: int, url: str, source_name: str = "") -> RecipeSource:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO recipe_sources (recipe_id, url, source_name) VALUES (?,?,?)
               ON CONFLICT(recipe_id) DO UPDATE SET url=?, source_name=?""",
            (recipe_id, url, source_name, url, source_name))
        conn.commit()
        row = conn.execute("SELECT * FROM recipe_sources WHERE recipe_id=?", (recipe_id,)).fetchone()
        conn.close()
        return RecipeSource(**dict(row))

    def get_recipe_source(self, recipe_id: int) -> RecipeSource | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM recipe_sources WHERE recipe_id=?", (recipe_id,)).fetchone()
        conn.close()
        return RecipeSource(**dict(row)) if row else None

    # --- Menu Suggestion (Feature 76) ---

    def get_menu_suggestions(self, meal_type: str = "lunch", limit: int = 5) -> list[Recipe]:
        conn = self._get_conn()
        time_filter = ""
        if meal_type == "breakfast":
            time_filter = "AND r.cooking_time_min <= 30"
        elif meal_type == "snack":
            time_filter = "AND r.cooking_time_min <= 15"
        rows = conn.execute(
            f"""SELECT r.*, u.username AS author_name FROM recipes r
                JOIN users u ON r.author_id=u.id
                WHERE r.is_public=1 {time_filter}
                ORDER BY r.rating_avg DESC, r.like_count DESC LIMIT ?""",
            (limit,)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Cost Log (Feature 77) ---

    def log_cooking_cost(self, user_id: int, recipe_id: int, amount: float, note: str = "") -> CostLog:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO cost_logs (user_id, recipe_id, amount, note, created_at) VALUES (?,?,?,?,?)",
            (user_id, recipe_id, amount, note, now))
        conn.commit()
        cid = cur.lastrowid
        conn.close()
        return CostLog(id=cid, user_id=user_id, recipe_id=recipe_id, amount=amount, note=note, created_at=now)

    def get_cost_logs(self, user_id: int, limit: int = 50) -> list[CostLog]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM cost_logs WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                            (user_id, limit)).fetchall()
        conn.close()
        return [CostLog(**dict(r)) for r in rows]

    def get_total_cost(self, user_id: int, days: int = 30) -> float:
        conn = self._get_conn()
        cutoff = time.time() - days * 86400
        row = conn.execute("SELECT COALESCE(SUM(amount),0) FROM cost_logs WHERE user_id=? AND created_at>=?",
                           (user_id, cutoff)).fetchone()
        conn.close()
        return row[0]

    # --- Recipe Reactions (Feature 78) ---

    def add_reaction(self, user_id: int, recipe_id: int, emoji: str) -> RecipeReaction:
        conn = self._get_conn()
        now = time.time()
        try:
            cur = conn.execute(
                "INSERT INTO recipe_reactions (user_id, recipe_id, emoji, created_at) VALUES (?,?,?,?)",
                (user_id, recipe_id, emoji, now))
            conn.commit()
            return RecipeReaction(id=cur.lastrowid, user_id=user_id, recipe_id=recipe_id, emoji=emoji, created_at=now)
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("이미 같은 리액션을 했습니다")

    def remove_reaction(self, user_id: int, recipe_id: int, emoji: str) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM recipe_reactions WHERE user_id=? AND recipe_id=? AND emoji=?",
                           (user_id, recipe_id, emoji))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    def get_reactions(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT emoji, COUNT(*) as cnt FROM recipe_reactions WHERE recipe_id=? GROUP BY emoji ORDER BY cnt DESC",
            (recipe_id,)).fetchall()
        conn.close()
        return [{"emoji": r["emoji"], "count": r["cnt"]} for r in rows]

    # --- Cooking Playlist (Feature 79) ---

    def create_playlist(self, user_id: int, name: str) -> CookingPlaylist:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("INSERT INTO cooking_playlists (user_id, name, created_at) VALUES (?,?,?)",
                           (user_id, name, now))
        conn.commit()
        pid = cur.lastrowid
        conn.close()
        return CookingPlaylist(id=pid, user_id=user_id, name=name, created_at=now)

    def add_to_playlist(self, playlist_id: int, recipe_id: int, sort_order: int = 0) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO playlist_items (playlist_id, recipe_id, sort_order) VALUES (?,?,?)",
                         (playlist_id, recipe_id, sort_order))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_playlist_recipes(self, playlist_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM playlist_items pi
               JOIN recipes r ON pi.recipe_id=r.id JOIN users u ON r.author_id=u.id
               WHERE pi.playlist_id=? ORDER BY pi.sort_order""",
            (playlist_id,)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_user_playlists(self, user_id: int) -> list[CookingPlaylist]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM cooking_playlists WHERE user_id=? ORDER BY created_at DESC",
                            (user_id,)).fetchall()
        conn.close()
        return [CookingPlaylist(**dict(r)) for r in rows]

    def delete_playlist(self, playlist_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM cooking_playlists WHERE id=? AND user_id=?", (playlist_id, user_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # --- Recipe Certification (Feature 80) ---

    def certify_recipe(self, recipe_id: int, certifier_id: int) -> RecipeCertification:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO recipe_certifications (recipe_id, certified_by, certified_at) VALUES (?,?,?)
               ON CONFLICT(recipe_id) DO UPDATE SET certified_by=?, certified_at=?""",
            (recipe_id, certifier_id, now, certifier_id, now))
        conn.commit()
        conn.close()
        return RecipeCertification(recipe_id=recipe_id, certified_by=certifier_id, certified_at=now)

    def is_certified(self, recipe_id: int) -> bool:
        conn = self._get_conn()
        row = conn.execute("SELECT 1 FROM recipe_certifications WHERE recipe_id=?", (recipe_id,)).fetchone()
        conn.close()
        return row is not None

    def get_certified_recipes(self, limit: int = 50) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM recipe_certifications rc
               JOIN recipes r ON rc.recipe_id=r.id JOIN users u ON r.author_id=u.id
               ORDER BY rc.certified_at DESC LIMIT ?""", (limit,)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Ingredient Season (Feature 81) ---

    def set_ingredient_season(self, name: str, seasons: list[str]) -> IngredientSeason:
        conn = self._get_conn()
        s = ",".join(seasons)
        conn.execute(
            """INSERT INTO ingredient_seasons (name, seasons) VALUES (?,?)
               ON CONFLICT(name) DO UPDATE SET seasons=?""", (name.strip().lower(), s, s))
        conn.commit()
        conn.close()
        return IngredientSeason(name=name.strip().lower(), seasons=s)

    def get_seasonal_ingredients(self, season: str) -> list[str]:
        conn = self._get_conn()
        rows = conn.execute("SELECT name FROM ingredient_seasons WHERE seasons LIKE ?",
                            (f"%{season}%",)).fetchall()
        conn.close()
        return [r["name"] for r in rows]

    # --- Timer Presets (Feature 82) ---

    def save_timer_preset(self, user_id: int, name: str, timers_json: str) -> TimerPreset:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO timer_presets (user_id, name, timers_json, created_at) VALUES (?,?,?,?)
               ON CONFLICT(user_id, name) DO UPDATE SET timers_json=?, created_at=?""",
            (user_id, name, timers_json, now, timers_json, now))
        conn.commit()
        row = conn.execute("SELECT * FROM timer_presets WHERE user_id=? AND name=?", (user_id, name)).fetchone()
        conn.close()
        return TimerPreset(**dict(row))

    def get_timer_presets(self, user_id: int) -> list[TimerPreset]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM timer_presets WHERE user_id=? ORDER BY created_at DESC",
                            (user_id,)).fetchall()
        conn.close()
        return [TimerPreset(**dict(r)) for r in rows]

    def delete_timer_preset(self, preset_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM timer_presets WHERE id=? AND user_id=?", (preset_id, user_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # --- Recipe Edit History (Feature 83) ---

    def log_recipe_edit(self, recipe_id: int, user_id: int, field_name: str, old_value: str, new_value: str) -> RecipeEditLog:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO recipe_edit_history (recipe_id, user_id, field_name, old_value, new_value, edited_at) VALUES (?,?,?,?,?,?)",
            (recipe_id, user_id, field_name, old_value, new_value, now))
        conn.commit()
        eid = cur.lastrowid
        conn.close()
        return RecipeEditLog(id=eid, recipe_id=recipe_id, user_id=user_id, field_name=field_name,
                             old_value=old_value, new_value=new_value, edited_at=now)

    def get_edit_history(self, recipe_id: int, limit: int = 50) -> list[RecipeEditLog]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM recipe_edit_history WHERE recipe_id=? ORDER BY edited_at DESC LIMIT ?",
                            (recipe_id, limit)).fetchall()
        conn.close()
        return [RecipeEditLog(**dict(r)) for r in rows]

    # --- Social Share Tracking (Feature 84) ---

    def track_social_share(self, recipe_id: int, platform: str) -> SocialShare:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("INSERT INTO social_shares (recipe_id, platform, shared_at) VALUES (?,?,?)",
                           (recipe_id, platform, now))
        conn.commit()
        sid = cur.lastrowid
        conn.close()
        return SocialShare(id=sid, recipe_id=recipe_id, platform=platform, shared_at=now)

    def get_social_shares(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT platform, COUNT(*) as cnt FROM social_shares WHERE recipe_id=? GROUP BY platform",
            (recipe_id,)).fetchall()
        conn.close()
        return [{"platform": r["platform"], "count": r["cnt"]} for r in rows]

    # --- Recipe Templates (Feature 85) ---

    def create_template(self, name: str, description: str, default_data_json: str) -> RecipeTemplate:
        conn = self._get_conn()
        now = time.time()
        try:
            cur = conn.execute(
                "INSERT INTO recipe_templates (name, description, default_data_json, created_at) VALUES (?,?,?,?)",
                (name, description, default_data_json, now))
            conn.commit()
            return RecipeTemplate(id=cur.lastrowid, name=name, description=description,
                                  default_data_json=default_data_json, created_at=now)
        except sqlite3.IntegrityError:
            raise ValueError("같은 이름의 템플릿이 존재합니다")
        finally:
            conn.close()

    def get_templates(self) -> list[RecipeTemplate]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM recipe_templates ORDER BY created_at DESC").fetchall()
        conn.close()
        return [RecipeTemplate(**dict(r)) for r in rows]

    def get_template(self, template_id: int) -> RecipeTemplate | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM recipe_templates WHERE id=?", (template_id,)).fetchone()
        conn.close()
        return RecipeTemplate(**dict(row)) if row else None

    # --- Cooking Skill (Feature 86) ---

    def set_cooking_skill(self, user_id: int, skill_level: str) -> dict:
        if skill_level not in ("beginner", "intermediate", "advanced", "expert"):
            raise ValueError("잘못된 스킬 레벨입니다")
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO cooking_skills (user_id, skill_level) VALUES (?,?)
               ON CONFLICT(user_id) DO UPDATE SET skill_level=?""",
            (user_id, skill_level, skill_level))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "skill_level": skill_level}

    def get_cooking_skill(self, user_id: int) -> str:
        conn = self._get_conn()
        row = conn.execute("SELECT skill_level FROM cooking_skills WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        return row["skill_level"] if row else "beginner"

    # --- Default Servings (Feature 87) ---

    def set_default_servings(self, user_id: int, servings: int) -> dict:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO serving_preferences (user_id, default_servings) VALUES (?,?)
               ON CONFLICT(user_id) DO UPDATE SET default_servings=?""",
            (user_id, servings, servings))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "default_servings": servings}

    def get_default_servings(self, user_id: int) -> int:
        conn = self._get_conn()
        row = conn.execute("SELECT default_servings FROM serving_preferences WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        return row["default_servings"] if row else 2

    # --- Recipe Archive (Feature 88) ---

    def archive_recipe(self, recipe_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO recipe_archives (recipe_id, user_id) VALUES (?,?)", (recipe_id, user_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def unarchive_recipe(self, recipe_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM recipe_archives WHERE recipe_id=? AND user_id=?", (recipe_id, user_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    def get_archived_recipes(self, user_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM recipe_archives ra
               JOIN recipes r ON ra.recipe_id=r.id JOIN users u ON r.author_id=u.id
               WHERE ra.user_id=? ORDER BY ra.archived_at DESC""", (user_id,)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Ingredient Usage Stats (Feature 89) ---

    def get_ingredient_usage_stats(self, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT name, COUNT(*) as cnt FROM ingredients GROUP BY LOWER(name) ORDER BY cnt DESC LIMIT ?",
            (limit,)).fetchall()
        conn.close()
        return [{"name": r["name"], "count": r["cnt"]} for r in rows]

    def get_user_ingredient_stats(self, user_id: int, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT i.name, COUNT(*) as cnt FROM ingredients i
               JOIN recipes r ON i.recipe_id=r.id WHERE r.author_id=?
               GROUP BY LOWER(i.name) ORDER BY cnt DESC LIMIT ?""",
            (user_id, limit)).fetchall()
        conn.close()
        return [{"name": r["name"], "count": r["cnt"]} for r in rows]

    # --- Auto Menu Plan (Feature 90) ---

    def generate_weekly_menu(self, user_id: int, start_date: str) -> list[dict]:
        conn = self._get_conn()
        recipes = conn.execute(
            "SELECT r.*, u.username AS author_name FROM recipes r JOIN users u ON r.author_id=u.id WHERE r.is_public=1 ORDER BY r.rating_avg DESC LIMIT 21"
        ).fetchall()
        conn.close()
        recipe_list = [Recipe(**dict(r)) for r in recipes]
        result = []
        meal_types = ["breakfast", "lunch", "dinner"]
        from datetime import datetime, timedelta
        base = datetime.strptime(start_date, "%Y-%m-%d")
        idx = 0
        for day in range(7):
            d = (base + timedelta(days=day)).strftime("%Y-%m-%d")
            for mt in meal_types:
                if idx < len(recipe_list):
                    self.set_meal_plan(user_id, d, mt, recipe_list[idx].id)
                    result.append({"date": d, "meal_type": mt, "recipe_id": recipe_list[idx].id, "title": recipe_list[idx].title})
                    idx += 1
        return result

    # --- Cost Compare (Feature 91) ---

    def compare_recipe_costs(self, recipe_ids: list[int]) -> list[dict]:
        results = []
        for rid in recipe_ids:
            cost_data = self.estimate_recipe_cost(rid)
            results.append({"recipe_id": rid, **cost_data})
        return sorted(results, key=lambda x: x.get("total_cost", 0))

    # --- Achievements V2 (Feature 92) ---

    def create_achievement(self, code: str, name: str, description: str, condition_type: str, condition_value: int) -> dict:
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO achievements (code, name, description, condition_type, condition_value) VALUES (?,?,?,?,?)",
                (code, name, description, condition_type, condition_value))
            conn.commit()
            return {"code": code, "name": name, "condition_type": condition_type}
        except sqlite3.IntegrityError:
            raise ValueError("이미 존재하는 업적입니다")
        finally:
            conn.close()

    def check_achievements(self, user_id: int) -> list[str]:
        conn = self._get_conn()
        achievements = conn.execute("SELECT * FROM achievements").fetchall()
        awarded = []
        for a in achievements:
            existing = conn.execute("SELECT 1 FROM user_achievements WHERE user_id=? AND achievement_id=?",
                                    (user_id, a["id"])).fetchone()
            if existing:
                continue
            met = False
            ct = a["condition_type"]
            cv = a["condition_value"]
            if ct == "recipes_created":
                cnt = conn.execute("SELECT COUNT(*) FROM recipes WHERE author_id=?", (user_id,)).fetchone()[0]
                met = cnt >= cv
            elif ct == "likes_received":
                cnt = conn.execute("SELECT COALESCE(SUM(like_count),0) FROM recipes WHERE author_id=?", (user_id,)).fetchone()[0]
                met = cnt >= cv
            elif ct == "cook_logs":
                cnt = conn.execute("SELECT COUNT(*) FROM cook_logs WHERE user_id=?", (user_id,)).fetchone()[0]
                met = cnt >= cv
            if met:
                conn.execute("INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?,?)",
                             (user_id, a["id"]))
                awarded.append(a["code"])
        conn.commit()
        conn.close()
        return awarded

    def get_user_achievements(self, user_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT a.code, a.name, a.description, ua.awarded_at FROM user_achievements ua
               JOIN achievements a ON ua.achievement_id=a.id WHERE ua.user_id=? ORDER BY ua.awarded_at DESC""",
            (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Hashtags (Feature 93) ---

    def add_hashtag(self, recipe_id: int, hashtag: str) -> dict:
        tag = hashtag.strip().lower().lstrip("#")
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO hashtags (recipe_id, hashtag) VALUES (?,?)", (recipe_id, tag))
            conn.commit()
            return {"recipe_id": recipe_id, "hashtag": tag}
        except sqlite3.IntegrityError:
            return {"recipe_id": recipe_id, "hashtag": tag, "exists": True}
        finally:
            conn.close()

    def remove_hashtag(self, recipe_id: int, hashtag: str) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM hashtags WHERE recipe_id=? AND hashtag=?",
                           (recipe_id, hashtag.strip().lower().lstrip("#")))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    def search_by_hashtag(self, hashtag: str, limit: int = 50) -> list[Recipe]:
        tag = hashtag.strip().lower().lstrip("#")
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM hashtags h
               JOIN recipes r ON h.recipe_id=r.id JOIN users u ON r.author_id=u.id
               WHERE h.hashtag=? ORDER BY r.created_at DESC LIMIT ?""", (tag, limit)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_trending_hashtags(self, limit: int = 10) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT hashtag, COUNT(*) as cnt FROM hashtags GROUP BY hashtag ORDER BY cnt DESC LIMIT ?",
            (limit,)).fetchall()
        conn.close()
        return [{"hashtag": r["hashtag"], "count": r["cnt"]} for r in rows]

    # --- Price Alert (Feature 94) ---

    def set_price_alert(self, user_id: int, ingredient: str, max_price: float) -> PriceAlert:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO price_alerts (user_id, ingredient, max_price, created_at) VALUES (?,?,?,?)
               ON CONFLICT(user_id, ingredient) DO UPDATE SET max_price=?, created_at=?""",
            (user_id, ingredient.lower(), max_price, now, max_price, now))
        conn.commit()
        conn.close()
        return PriceAlert(user_id=user_id, ingredient=ingredient.lower(), max_price=max_price, created_at=now)

    def get_price_alerts(self, user_id: int) -> list[PriceAlert]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM price_alerts WHERE user_id=?", (user_id,)).fetchall()
        conn.close()
        return [PriceAlert(**dict(r)) for r in rows]

    def check_price_alerts(self, user_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT pa.ingredient, pa.max_price, ip.price as current_price FROM price_alerts pa
               JOIN ingredient_prices ip ON LOWER(ip.name)=pa.ingredient
               WHERE pa.user_id=? AND ip.price <= pa.max_price""", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Recipe Collaboration (Feature 95) ---

    def invite_collaborator(self, recipe_id: int, user_id: int, role: str = "editor") -> dict:
        conn = self._get_conn()
        now = time.time()
        try:
            conn.execute("INSERT INTO recipe_collaborators (recipe_id, user_id, role, added_at) VALUES (?,?,?,?)",
                         (recipe_id, user_id, role, now))
            conn.commit()
            return {"recipe_id": recipe_id, "user_id": user_id, "role": role}
        except sqlite3.IntegrityError:
            raise ValueError("이미 협업자입니다")
        finally:
            conn.close()

    def get_collaborators(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT rc.user_id, u.username, rc.role, rc.added_at FROM recipe_collaborators rc
               JOIN users u ON rc.user_id=u.id WHERE rc.recipe_id=?""", (recipe_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def remove_collaborator(self, recipe_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM recipe_collaborators WHERE recipe_id=? AND user_id=?", (recipe_id, user_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # --- Cooking Class (Feature 96) ---

    def create_cooking_class(self, title: str, description: str, instructor_id: int,
                              scheduled_date: str, max_participants: int = 20) -> CookingClass:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO cooking_classes (title, description, instructor_id, scheduled_date, max_participants, created_at) VALUES (?,?,?,?,?,?)",
            (title, description, instructor_id, scheduled_date, max_participants, now))
        conn.commit()
        cid = cur.lastrowid
        conn.close()
        return CookingClass(id=cid, title=title, description=description, instructor_id=instructor_id,
                             scheduled_date=scheduled_date, max_participants=max_participants, created_at=now)

    def join_cooking_class(self, class_id: int, user_id: int) -> dict:
        conn = self._get_conn()
        cnt = conn.execute("SELECT COUNT(*) FROM class_registrations WHERE class_id=?", (class_id,)).fetchone()[0]
        cls = conn.execute("SELECT max_participants FROM cooking_classes WHERE id=?", (class_id,)).fetchone()
        if not cls:
            conn.close()
            raise ValueError("클래스를 찾을 수 없습니다")
        if cnt >= cls["max_participants"]:
            conn.close()
            raise ValueError("정원이 초과되었습니다")
        try:
            conn.execute("INSERT INTO class_registrations (class_id, user_id) VALUES (?,?)", (class_id, user_id))
            conn.commit()
            return {"class_id": class_id, "user_id": user_id, "participants": cnt + 1}
        except sqlite3.IntegrityError:
            raise ValueError("이미 등록되었습니다")
        finally:
            conn.close()

    def get_cooking_classes(self, upcoming_only: bool = True) -> list[CookingClass]:
        conn = self._get_conn()
        if upcoming_only:
            from datetime import date
            today = date.today().isoformat()
            rows = conn.execute("SELECT * FROM cooking_classes WHERE scheduled_date>=? ORDER BY scheduled_date",
                                (today,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM cooking_classes ORDER BY scheduled_date DESC").fetchall()
        conn.close()
        return [CookingClass(**dict(r)) for r in rows]

    def get_class_participants(self, class_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT u.id, u.username, cr.registered_at FROM class_registrations cr
               JOIN users u ON cr.user_id=u.id WHERE cr.class_id=?""", (class_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Recipe Bundle (Feature 97) ---

    def create_bundle(self, user_id: int, name: str, description: str = "") -> RecipeBundle:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("INSERT INTO recipe_bundles (name, description, created_by, created_at) VALUES (?,?,?,?)",
                           (name, description, user_id, now))
        conn.commit()
        bid = cur.lastrowid
        conn.close()
        return RecipeBundle(id=bid, name=name, description=description, created_by=user_id, created_at=now)

    def add_to_bundle(self, bundle_id: int, recipe_id: int, sort_order: int = 0) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO bundle_items (bundle_id, recipe_id, sort_order) VALUES (?,?,?)",
                         (bundle_id, recipe_id, sort_order))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_bundle_recipes(self, bundle_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM bundle_items bi
               JOIN recipes r ON bi.recipe_id=r.id JOIN users u ON r.author_id=u.id
               WHERE bi.bundle_id=? ORDER BY bi.sort_order""", (bundle_id,)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_bundles(self) -> list[RecipeBundle]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM recipe_bundles ORDER BY created_at DESC").fetchall()
        conn.close()
        return [RecipeBundle(**dict(r)) for r in rows]

    # --- Meal Prep (Feature 98) ---

    def create_meal_prep(self, user_id: int, name: str, prep_date: str, servings: int = 4) -> MealPrep:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("INSERT INTO meal_preps (user_id, name, prep_date, servings, created_at) VALUES (?,?,?,?,?)",
                           (user_id, name, prep_date, servings, now))
        conn.commit()
        pid = cur.lastrowid
        conn.close()
        return MealPrep(id=pid, user_id=user_id, name=name, prep_date=prep_date, servings=servings, created_at=now)

    def add_meal_prep_recipe(self, prep_id: int, recipe_id: int) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO meal_prep_recipes (prep_id, recipe_id) VALUES (?,?)", (prep_id, recipe_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_meal_prep_recipes(self, prep_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM meal_prep_recipes mpr
               JOIN recipes r ON mpr.recipe_id=r.id JOIN users u ON r.author_id=u.id
               WHERE mpr.prep_id=?""", (prep_id,)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_user_meal_preps(self, user_id: int) -> list[MealPrep]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM meal_preps WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
        conn.close()
        return [MealPrep(**dict(r)) for r in rows]

    # --- Recipe Analytics (Feature 99) ---

    def get_recipe_analytics(self, recipe_id: int) -> dict:
        conn = self._get_conn()
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            conn.close()
            raise ValueError("레시피를 찾을 수 없습니다")
        comment_cnt = conn.execute("SELECT COUNT(*) FROM comments WHERE recipe_id=?", (recipe_id,)).fetchone()[0]
        cook_cnt = conn.execute("SELECT COUNT(*) FROM cook_logs WHERE recipe_id=?", (recipe_id,)).fetchone()[0]
        conn.close()
        return {
            "recipe_id": recipe_id, "title": recipe.title,
            "views": recipe.view_count, "likes": recipe.like_count,
            "bookmarks": recipe.bookmark_count, "comments": comment_cnt,
            "cook_logs": cook_cnt, "rating_avg": recipe.rating_avg,
            "rating_count": recipe.rating_count, "forks": recipe.fork_count,
        }

    def get_author_analytics(self, user_id: int) -> dict:
        conn = self._get_conn()
        stats = conn.execute(
            """SELECT COUNT(*) as total, COALESCE(SUM(like_count),0) as likes,
               COALESCE(SUM(view_count),0) as views, COALESCE(AVG(rating_avg),0) as avg_rating
               FROM recipes WHERE author_id=?""", (user_id,)).fetchone()
        follower_cnt = conn.execute("SELECT COUNT(*) FROM follows WHERE following_id=?", (user_id,)).fetchone()[0]
        conn.close()
        return {"user_id": user_id, "total_recipes": stats["total"], "total_likes": stats["likes"],
                "total_views": stats["views"], "avg_rating": round(stats["avg_rating"], 2),
                "followers": follower_cnt}

    # --- Flavor Profile (Feature 100) ---

    def set_flavor_profile(self, recipe_id: int, sweet: int = 0, salty: int = 0, sour: int = 0,
                            bitter: int = 0, umami: int = 0, spicy: int = 0) -> dict:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO flavor_profiles (recipe_id, sweet, salty, sour, bitter, umami, spicy) VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(recipe_id) DO UPDATE SET sweet=?, salty=?, sour=?, bitter=?, umami=?, spicy=?""",
            (recipe_id, sweet, salty, sour, bitter, umami, spicy, sweet, salty, sour, bitter, umami, spicy))
        conn.commit()
        conn.close()
        return {"recipe_id": recipe_id, "sweet": sweet, "salty": salty, "sour": sour,
                "bitter": bitter, "umami": umami, "spicy": spicy}

    def get_flavor_profile(self, recipe_id: int) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM flavor_profiles WHERE recipe_id=?", (recipe_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return {"sweet": row["sweet"], "salty": row["salty"], "sour": row["sour"],
                "bitter": row["bitter"], "umami": row["umami"], "spicy": row["spicy"]}

    def find_by_flavor(self, flavor: str, min_score: int = 3, limit: int = 20) -> list[Recipe]:
        if flavor not in ("sweet", "salty", "sour", "bitter", "umami", "spicy"):
            return []
        conn = self._get_conn()
        rows = conn.execute(
            f"""SELECT r.*, u.username AS author_name FROM flavor_profiles fp
                JOIN recipes r ON fp.recipe_id=r.id JOIN users u ON r.author_id=u.id
                WHERE fp.{flavor} >= ? ORDER BY fp.{flavor} DESC LIMIT ?""",
            (min_score, limit)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Approval Queue (Feature 101) ---

    def submit_for_approval(self, recipe_id: int, user_id: int) -> dict:
        conn = self._get_conn()
        now = time.time()
        try:
            conn.execute("INSERT INTO approval_queue (recipe_id, submitted_by, submitted_at) VALUES (?,?,?)",
                         (recipe_id, user_id, now))
            conn.commit()
            return {"recipe_id": recipe_id, "status": "pending"}
        except sqlite3.IntegrityError:
            raise ValueError("이미 승인 요청 중입니다")
        finally:
            conn.close()

    def approve_recipe_submission(self, recipe_id: int, reviewer_id: int) -> dict:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "UPDATE approval_queue SET status='approved', reviewer_id=?, reviewed_at=? WHERE recipe_id=? AND status='pending'",
            (reviewer_id, now, recipe_id))
        conn.commit()
        conn.close()
        return {"recipe_id": recipe_id, "status": "approved", "updated": cur.rowcount > 0}

    def reject_recipe_submission(self, recipe_id: int, reviewer_id: int, reason: str = "") -> dict:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "UPDATE approval_queue SET status='rejected', reviewer_id=?, reason=?, reviewed_at=? WHERE recipe_id=? AND status='pending'",
            (reviewer_id, reason, now, recipe_id))
        conn.commit()
        conn.close()
        return {"recipe_id": recipe_id, "status": "rejected", "updated": cur.rowcount > 0}

    def get_pending_approvals(self, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT aq.*, r.title FROM approval_queue aq
               JOIN recipes r ON aq.recipe_id=r.id WHERE aq.status='pending'
               ORDER BY aq.submitted_at LIMIT ?""", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Cooking Journal (Feature 102) ---

    def add_journal_entry(self, user_id: int, date: str, content: str,
                           recipe_id: int | None = None, mood: str = "") -> JournalEntry:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO cooking_journal (user_id, date, content, recipe_id, mood, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, date, content, recipe_id, mood, now))
        conn.commit()
        jid = cur.lastrowid
        conn.close()
        return JournalEntry(id=jid, user_id=user_id, date=date, content=content,
                             recipe_id=recipe_id, mood=mood, created_at=now)

    def get_journal_entries(self, user_id: int, start_date: str | None = None,
                             end_date: str | None = None, limit: int = 50) -> list[JournalEntry]:
        conn = self._get_conn()
        query = "SELECT * FROM cooking_journal WHERE user_id=?"
        params: list = [user_id]
        if start_date:
            query += " AND date>=?"
            params.append(start_date)
        if end_date:
            query += " AND date<=?"
            params.append(end_date)
        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [JournalEntry(**dict(r)) for r in rows]

    # --- Remix Chain (Feature 103) ---

    def get_remix_chain(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        chain = []
        current = recipe_id
        while current:
            row = conn.execute(
                "SELECT r.id, r.title, r.forked_from_id, u.username AS author_name FROM recipes r JOIN users u ON r.author_id=u.id WHERE r.id=?",
                (current,)).fetchone()
            if not row:
                break
            chain.append(dict(row))
            current = row["forked_from_id"]
        conn.close()
        chain.reverse()
        return chain

    def get_remix_tree(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT r.id, r.title, u.username AS author_name FROM recipes r JOIN users u ON r.author_id=u.id WHERE r.forked_from_id=?",
            (recipe_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Ingredient Pairing (Feature 104) ---

    def add_ingredient_pairing(self, ing_a: str, ing_b: str, score: int = 5) -> dict:
        a, b = sorted([ing_a.lower().strip(), ing_b.lower().strip()])
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO ingredient_pairings (ingredient_a, ingredient_b, score) VALUES (?,?,?)
               ON CONFLICT(ingredient_a, ingredient_b) DO UPDATE SET score=?""",
            (a, b, score, score))
        conn.commit()
        conn.close()
        return {"ingredient_a": a, "ingredient_b": b, "score": score}

    def get_pairings(self, ingredient: str, limit: int = 10) -> list[dict]:
        ing = ingredient.lower().strip()
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM ingredient_pairings WHERE ingredient_a=? OR ingredient_b=?
               ORDER BY score DESC LIMIT ?""", (ing, ing, limit)).fetchall()
        conn.close()
        result = []
        for r in rows:
            other = r["ingredient_b"] if r["ingredient_a"] == ing else r["ingredient_a"]
            result.append({"ingredient": other, "score": r["score"]})
        return result

    def suggest_pairings(self, recipe_id: int, limit: int = 5) -> list[dict]:
        ings = self.get_recipe_ingredients(recipe_id)
        names = [i.name.lower().strip() for i in ings]
        suggestions = {}
        for name in names:
            pairs = self.get_pairings(name, limit=limit)
            for p in pairs:
                if p["ingredient"] not in names and p["ingredient"] not in suggestions:
                    suggestions[p["ingredient"]] = p["score"]
        return sorted([{"ingredient": k, "score": v} for k, v in suggestions.items()],
                      key=lambda x: x["score"], reverse=True)[:limit]

    # --- Mood Tags (Feature 105) ---

    def set_mood_tags(self, recipe_id: int, moods: list[str]) -> list[str]:
        conn = self._get_conn()
        conn.execute("DELETE FROM mood_tags WHERE recipe_id=?", (recipe_id,))
        for m in moods:
            conn.execute("INSERT INTO mood_tags (recipe_id, mood) VALUES (?,?)", (recipe_id, m.lower().strip()))
        conn.commit()
        conn.close()
        return [m.lower().strip() for m in moods]

    def get_mood_tags(self, recipe_id: int) -> list[str]:
        conn = self._get_conn()
        rows = conn.execute("SELECT mood FROM mood_tags WHERE recipe_id=?", (recipe_id,)).fetchall()
        conn.close()
        return [r["mood"] for r in rows]

    def find_by_mood(self, mood: str, limit: int = 50) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM mood_tags mt
               JOIN recipes r ON mt.recipe_id=r.id JOIN users u ON r.author_id=u.id
               WHERE mt.mood=? ORDER BY r.rating_avg DESC LIMIT ?""",
            (mood.lower().strip(), limit)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Speed Challenge (Feature 106) ---

    def create_speed_challenge(self, recipe_id: int, target_minutes: int) -> dict:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("INSERT INTO speed_challenges (recipe_id, target_minutes, created_at) VALUES (?,?,?)",
                           (recipe_id, target_minutes, now))
        conn.commit()
        cid = cur.lastrowid
        conn.close()
        return {"id": cid, "recipe_id": recipe_id, "target_minutes": target_minutes}

    def submit_speed_result(self, challenge_id: int, user_id: int, actual_minutes: int) -> dict:
        conn = self._get_conn()
        now = time.time()
        try:
            conn.execute("INSERT INTO speed_results (challenge_id, user_id, actual_minutes, created_at) VALUES (?,?,?,?)",
                         (challenge_id, user_id, actual_minutes, now))
            conn.commit()
            return {"challenge_id": challenge_id, "actual_minutes": actual_minutes}
        except sqlite3.IntegrityError:
            raise ValueError("이미 결과를 제출했습니다")
        finally:
            conn.close()

    def get_speed_rankings(self, challenge_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT sr.actual_minutes, u.username FROM speed_results sr
               JOIN users u ON sr.user_id=u.id WHERE sr.challenge_id=?
               ORDER BY sr.actual_minutes ASC""", (challenge_id,)).fetchall()
        conn.close()
        return [{"rank": i + 1, "username": r["username"], "actual_minutes": r["actual_minutes"]}
                for i, r in enumerate(rows)]

    # --- Recipe Gift (Feature 107) ---

    def send_recipe_gift(self, sender_id: int, recipient_id: int, recipe_id: int, message: str = "") -> dict:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO recipe_gifts (sender_id, recipient_id, recipe_id, message, created_at) VALUES (?,?,?,?,?)",
            (sender_id, recipient_id, recipe_id, message, now))
        conn.commit()
        gid = cur.lastrowid
        conn.close()
        return {"id": gid, "sender_id": sender_id, "recipient_id": recipient_id, "recipe_id": recipe_id}

    def get_received_gifts(self, user_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT rg.*, u.username AS sender_name, r.title AS recipe_title
               FROM recipe_gifts rg JOIN users u ON rg.sender_id=u.id
               JOIN recipes r ON rg.recipe_id=r.id
               WHERE rg.recipient_id=? ORDER BY rg.created_at DESC""", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_sent_gifts(self, user_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT rg.*, u.username AS recipient_name, r.title AS recipe_title
               FROM recipe_gifts rg JOIN users u ON rg.recipient_id=u.id
               JOIN recipes r ON rg.recipe_id=r.id
               WHERE rg.sender_id=? ORDER BY rg.created_at DESC""", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def open_gift(self, gift_id: int, user_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.execute("UPDATE recipe_gifts SET is_opened=1 WHERE id=? AND recipient_id=? AND is_opened=0",
                           (gift_id, user_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    # --- Ingredient Wiki (Feature 108) ---

    def add_ingredient_info(self, name: str, description: str = "", tips: str = "", storage: str = "") -> dict:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO ingredient_wiki (name, description, tips, storage, created_at) VALUES (?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET description=?, tips=?, storage=?""",
            (name.lower().strip(), description, tips, storage, now, description, tips, storage))
        conn.commit()
        conn.close()
        return {"name": name.lower().strip(), "description": description, "tips": tips, "storage": storage}

    def get_ingredient_info(self, name: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM ingredient_wiki WHERE name=?", (name.lower().strip(),)).fetchone()
        conn.close()
        return dict(row) if row else None

    def search_ingredient_wiki(self, query: str, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM ingredient_wiki WHERE name LIKE ? OR description LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Recipe Calendar (Feature 109) ---

    def get_recipe_calendar(self, user_id: int, year: int, month: int) -> dict:
        start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1:04d}-01-31"
        else:
            end = f"{year:04d}-{month + 1:02d}-01"
        plans = self.get_meal_plans(user_id, start, end)
        days: dict[str, list] = {}
        for p in plans:
            days.setdefault(p.date, []).append({"meal_type": p.meal_type, "recipe_id": p.recipe_id})
        return {"year": year, "month": month, "days": days}

    # --- Cooking Technique (Feature 110) ---

    def add_technique(self, name: str, description: str = "", difficulty: str = "easy") -> dict:
        conn = self._get_conn()
        try:
            cur = conn.execute("INSERT INTO cooking_techniques (name, description, difficulty) VALUES (?,?,?)",
                               (name, description, difficulty))
            conn.commit()
            return {"id": cur.lastrowid, "name": name, "description": description, "difficulty": difficulty}
        except sqlite3.IntegrityError:
            raise ValueError("이미 존재하는 기법입니다")
        finally:
            conn.close()

    def get_techniques(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM cooking_techniques ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def link_technique_to_recipe(self, recipe_id: int, technique_id: int) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO recipe_techniques (recipe_id, technique_id) VALUES (?,?)",
                         (recipe_id, technique_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_recipe_techniques(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT ct.* FROM recipe_techniques rt JOIN cooking_techniques ct ON rt.technique_id=ct.id
               WHERE rt.recipe_id=?""", (recipe_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Chef Endorsement (Feature 111) ---

    def endorse_recipe(self, user_id: int, recipe_id: int, comment: str = "") -> dict:
        conn = self._get_conn()
        now = time.time()
        try:
            conn.execute("INSERT INTO chef_endorsements (recipe_id, user_id, comment, created_at) VALUES (?,?,?,?)",
                         (recipe_id, user_id, comment, now))
            conn.commit()
            return {"recipe_id": recipe_id, "endorsed_by": user_id}
        except sqlite3.IntegrityError:
            raise ValueError("이미 추천했습니다")
        finally:
            conn.close()

    def get_endorsements(self, recipe_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT ce.comment, ce.created_at, u.username FROM chef_endorsements ce
               JOIN users u ON ce.user_id=u.id WHERE ce.recipe_id=? ORDER BY ce.created_at DESC""",
            (recipe_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_endorsed_recipes(self, limit: int = 50) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name, COUNT(ce.id) as endorsement_count
               FROM chef_endorsements ce JOIN recipes r ON ce.recipe_id=r.id
               JOIN users u ON r.author_id=u.id GROUP BY ce.recipe_id
               ORDER BY endorsement_count DESC LIMIT ?""", (limit,)).fetchall()
        conn.close()
        return [Recipe(**{k: v for k, v in dict(r).items() if k != "endorsement_count"}) for r in rows]

    # --- Ingredient Origin (Feature 112) ---

    def set_ingredient_origin(self, name: str, origin: str, description: str = "") -> dict:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO ingredient_origins (name, origin, description) VALUES (?,?,?)
               ON CONFLICT(name) DO UPDATE SET origin=?, description=?""",
            (name.lower().strip(), origin, description, origin, description))
        conn.commit()
        conn.close()
        return {"name": name.lower().strip(), "origin": origin, "description": description}

    def get_ingredient_origin(self, name: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM ingredient_origins WHERE name=?", (name.lower().strip(),)).fetchone()
        conn.close()
        return dict(row) if row else None

    # --- Event Recipe (Feature 113) ---

    def create_event(self, name: str, event_date: str, description: str = "") -> dict:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("INSERT INTO events (name, event_date, description, created_at) VALUES (?,?,?,?)",
                           (name, event_date, description, now))
        conn.commit()
        eid = cur.lastrowid
        conn.close()
        return {"id": eid, "name": name, "event_date": event_date}

    def link_recipe_to_event(self, event_id: int, recipe_id: int) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("INSERT INTO event_recipes (event_id, recipe_id) VALUES (?,?)", (event_id, recipe_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_event_recipes(self, event_id: int) -> list[Recipe]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT r.*, u.username AS author_name FROM event_recipes er
               JOIN recipes r ON er.recipe_id=r.id JOIN users u ON r.author_id=u.id
               WHERE er.event_id=?""", (event_id,)).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    def get_upcoming_events(self, limit: int = 10) -> list[dict]:
        conn = self._get_conn()
        from datetime import date
        today = date.today().isoformat()
        rows = conn.execute("SELECT * FROM events WHERE event_date>=? ORDER BY event_date LIMIT ?",
                            (today, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Group Cook (Feature 114) ---

    def create_group_cook(self, recipe_id: int, host_id: int, cook_date: str, max_participants: int = 8) -> dict:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO group_cooks (recipe_id, host_id, cook_date, max_participants, created_at) VALUES (?,?,?,?,?)",
            (recipe_id, host_id, cook_date, max_participants, now))
        conn.commit()
        gid = cur.lastrowid
        conn.close()
        return {"id": gid, "recipe_id": recipe_id, "cook_date": cook_date}

    def join_group_cook(self, group_id: int, user_id: int) -> dict:
        conn = self._get_conn()
        cnt = conn.execute("SELECT COUNT(*) FROM group_cook_members WHERE group_id=?", (group_id,)).fetchone()[0]
        gc = conn.execute("SELECT max_participants FROM group_cooks WHERE id=?", (group_id,)).fetchone()
        if not gc:
            conn.close()
            raise ValueError("그룹 쿠킹을 찾을 수 없습니다")
        if cnt >= gc["max_participants"]:
            conn.close()
            raise ValueError("정원 초과")
        try:
            conn.execute("INSERT INTO group_cook_members (group_id, user_id) VALUES (?,?)", (group_id, user_id))
            conn.commit()
            return {"group_id": group_id, "members": cnt + 1}
        except sqlite3.IntegrityError:
            raise ValueError("이미 참여 중입니다")
        finally:
            conn.close()

    def get_group_cooks(self, upcoming_only: bool = True) -> list[dict]:
        conn = self._get_conn()
        if upcoming_only:
            from datetime import date
            today = date.today().isoformat()
            rows = conn.execute("SELECT * FROM group_cooks WHERE cook_date>=? ORDER BY cook_date", (today,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM group_cooks ORDER BY cook_date DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_group_members(self, group_id: int) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT u.id, u.username, gcm.joined_at FROM group_cook_members gcm
               JOIN users u ON gcm.user_id=u.id WHERE gcm.group_id=?""", (group_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Nutrition Match (Feature 115) ---

    def find_nutrition_matching(self, target_calories: int | None = None, target_protein: float | None = None,
                                 tolerance: float = 0.2, limit: int = 20) -> list[Recipe]:
        conn = self._get_conn()
        query = """SELECT r.*, u.username AS author_name FROM nutrition_info ni
                   JOIN recipes r ON ni.recipe_id=r.id JOIN users u ON r.author_id=u.id WHERE 1=1"""
        params: list = []
        if target_calories:
            low, high = target_calories * (1 - tolerance), target_calories * (1 + tolerance)
            query += " AND ni.calories BETWEEN ? AND ?"
            params.extend([low, high])
        if target_protein:
            low, high = target_protein * (1 - tolerance), target_protein * (1 + tolerance)
            query += " AND ni.protein_g BETWEEN ? AND ?"
            params.extend([low, high])
        query += " LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [Recipe(**dict(r)) for r in rows]

    # --- Store Info (Feature 116) ---

    def add_store(self, name: str, location: str = "", description: str = "") -> dict:
        conn = self._get_conn()
        cur = conn.execute("INSERT INTO stores (name, location, description) VALUES (?,?,?)",
                           (name, location, description))
        conn.commit()
        sid = cur.lastrowid
        conn.close()
        return {"id": sid, "name": name, "location": location}

    def link_ingredient_to_store(self, store_id: int, ingredient: str, price: float = 0) -> dict:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO store_ingredients (store_id, ingredient, price) VALUES (?,?,?)
               ON CONFLICT(store_id, ingredient) DO UPDATE SET price=?""",
            (store_id, ingredient.lower(), price, price))
        conn.commit()
        conn.close()
        return {"store_id": store_id, "ingredient": ingredient.lower(), "price": price}

    def find_stores_for_ingredient(self, ingredient: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT s.name, s.location, si.price FROM store_ingredients si
               JOIN stores s ON si.store_id=s.id WHERE si.ingredient=? ORDER BY si.price""",
            (ingredient.lower(),)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Recipe Story (Feature 117) ---

    def set_recipe_story(self, recipe_id: int, story: str) -> dict:
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """INSERT INTO recipe_stories (recipe_id, story, created_at) VALUES (?,?,?)
               ON CONFLICT(recipe_id) DO UPDATE SET story=?, created_at=?""",
            (recipe_id, story, now, story, now))
        conn.commit()
        conn.close()
        return {"recipe_id": recipe_id, "story": story}

    def get_recipe_story(self, recipe_id: int) -> str | None:
        conn = self._get_conn()
        row = conn.execute("SELECT story FROM recipe_stories WHERE recipe_id=?", (recipe_id,)).fetchone()
        conn.close()
        return row["story"] if row else None

    # --- Cooking FAQ (Feature 118) ---

    def add_faq(self, question: str, answer: str, category: str = "general") -> dict:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("INSERT INTO cooking_faqs (question, answer, category, created_at) VALUES (?,?,?,?)",
                           (question, answer, category, now))
        conn.commit()
        fid = cur.lastrowid
        conn.close()
        return {"id": fid, "question": question, "answer": answer, "category": category}

    def get_faqs(self, category: str | None = None, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        if category:
            rows = conn.execute("SELECT * FROM cooking_faqs WHERE category=? ORDER BY created_at DESC LIMIT ?",
                                (category, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM cooking_faqs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def search_faqs(self, query: str, limit: int = 10) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM cooking_faqs WHERE question LIKE ? OR answer LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Recipe Ranking (Feature 119) ---

    def get_recipe_rankings(self, category: str | None = None, period: str = "all", limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        where_parts = ["r.is_public=1"]
        params: list = []
        if category:
            where_parts.append("r.category=?")
            params.append(category)
        if period == "week":
            where_parts.append("r.created_at>=?")
            params.append(time.time() - 7 * 86400)
        elif period == "month":
            where_parts.append("r.created_at>=?")
            params.append(time.time() - 30 * 86400)
        where = " AND ".join(where_parts)
        params.append(limit)
        rows = conn.execute(
            f"""SELECT r.id, r.title, r.like_count, r.rating_avg, r.view_count, r.bookmark_count,
                (r.like_count*3 + r.rating_avg*20 + r.view_count + r.bookmark_count*5) as score
                FROM recipes r WHERE {where} ORDER BY score DESC LIMIT ?""",
            params).fetchall()
        conn.close()
        return [{"rank": i + 1, **dict(r)} for i, r in enumerate(rows)]

    # --- Weekly Digest (Feature 120) ---

    def generate_weekly_digest(self, user_id: int) -> dict:
        conn = self._get_conn()
        week_ago = time.time() - 7 * 86400
        following_recipes = conn.execute(
            """SELECT r.id, r.title, u.username AS author_name FROM recipes r
               JOIN follows f ON r.author_id=f.following_id
               JOIN users u ON r.author_id=u.id
               WHERE f.follower_id=? AND r.created_at>=? ORDER BY r.created_at DESC LIMIT 10""",
            (user_id, week_ago)).fetchall()
        popular = conn.execute(
            """SELECT r.id, r.title FROM recipes r WHERE r.created_at>=? AND r.is_public=1
               ORDER BY r.like_count DESC LIMIT 5""", (week_ago,)).fetchall()
        new_followers = conn.execute(
            "SELECT COUNT(*) FROM follows WHERE following_id=? AND created_at>=?",
            (user_id, week_ago)).fetchone()[0]
        conn.close()
        return {
            "new_from_following": [dict(r) for r in following_recipes],
            "popular_this_week": [dict(r) for r in popular],
            "new_followers": new_followers,
        }
