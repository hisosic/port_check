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


# --- Point configuration ---
POINTS_RECIPE_CREATED = 10
POINTS_RECIPE_LIKED = 2
POINTS_FIRST_RECIPE_BONUS = 20
POINTS_COMMENT_WRITTEN = 3
POINTS_RATING_GIVEN = 1
POINTS_COOK_LOGGED = 2
POINTS_REPLY_WRITTEN = 1


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
