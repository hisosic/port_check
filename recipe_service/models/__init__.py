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


# --- Point configuration ---
POINTS_RECIPE_CREATED = 10
POINTS_RECIPE_LIKED = 2
POINTS_FIRST_RECIPE_BONUS = 20
POINTS_COMMENT_WRITTEN = 3
POINTS_RATING_GIVEN = 1
POINTS_COOK_LOGGED = 2


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
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
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
