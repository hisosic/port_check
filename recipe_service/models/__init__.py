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


# --- Point configuration ---
POINTS_RECIPE_CREATED = 10
POINTS_RECIPE_LIKED = 2
POINTS_FIRST_RECIPE_BONUS = 20
POINTS_COMMENT_WRITTEN = 3
POINTS_RATING_GIVEN = 1


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
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (author_id) REFERENCES users(id)
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
