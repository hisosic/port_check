"""FridgeChef - FastAPI Application.

냉장고 재료 기반 레시피 추천 + 유저 레시피 등록 + 포인트 시스템
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from http import HTTPStatus
from typing import Any

from recipe_service.api import get_db
from recipe_service.models import Database, User
from recipe_service.services.auth import (
    generate_token,
    get_current_user,
    login_user,
    register_user,
    revoke_token,
    validate_token,
)


def create_app():
    """Create and configure the FastAPI application."""
    try:
        from fastapi import FastAPI, Header, HTTPException, Query
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel, Field
    except ImportError:
        # Fallback: create a simple WSGI-like app without FastAPI
        return _create_simple_app()

    app = FastAPI(
        title="FridgeChef API",
        description="냉장고 재료 기반 레시피 추천 서비스",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db = get_db()

    # --- Pydantic Models ---

    class RegisterRequest(BaseModel):
        username: str = Field(min_length=2, max_length=30)
        email: str
        password: str = Field(min_length=4)

    class LoginRequest(BaseModel):
        username: str
        password: str

    class IngredientInput(BaseModel):
        name: str
        amount: str = ""
        unit: str = ""

    class RecipeCreateRequest(BaseModel):
        title: str = Field(min_length=1, max_length=200)
        description: str = ""
        instructions: str = Field(min_length=1)
        ingredients: list[IngredientInput] = Field(min_length=1)
        cooking_time_min: int = Field(ge=0, default=0)
        servings: int = Field(ge=1, default=1)
        difficulty: str = Field(default="easy", pattern="^(easy|medium|hard)$")

    class IngredientSearchRequest(BaseModel):
        ingredients: list[str] = Field(min_length=1, description="냉장고에 있는 재료 목록")
        min_match_ratio: float = Field(ge=0.0, le=1.0, default=0.3)

    class CommentCreateRequest(BaseModel):
        content: str = Field(min_length=1, max_length=2000)

    class CommentUpdateRequest(BaseModel):
        content: str = Field(min_length=1, max_length=2000)

    class RatingRequest(BaseModel):
        score: int = Field(ge=1, le=5, description="별점 1~5")

    # --- Auth helpers ---

    def _get_user(authorization: str | None) -> User:
        if not authorization:
            raise HTTPException(401, "인증이 필요합니다")
        token = authorization.replace("Bearer ", "")
        try:
            return get_current_user(db, token)
        except PermissionError as e:
            raise HTTPException(401, str(e))

    def _get_optional_user(authorization: str | None) -> User | None:
        if not authorization:
            return None
        token = authorization.replace("Bearer ", "")
        user_id = validate_token(token)
        if not user_id:
            return None
        return db.get_user(user_id)

    # =====================
    # AUTH ENDPOINTS
    # =====================

    @app.post("/api/auth/register", tags=["auth"])
    def api_register(req: RegisterRequest):
        """회원가입"""
        try:
            result = register_user(db, req.username, req.email, req.password)
            return {"success": True, **result}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/auth/login", tags=["auth"])
    def api_login(req: LoginRequest):
        """로그인"""
        try:
            result = login_user(db, req.username, req.password)
            return {"success": True, **result}
        except ValueError as e:
            raise HTTPException(401, str(e))

    @app.post("/api/auth/logout", tags=["auth"])
    def api_logout(authorization: str | None = Header(None)):
        """로그아웃"""
        if authorization:
            token = authorization.replace("Bearer ", "")
            revoke_token(token)
        return {"success": True}

    @app.get("/api/auth/me", tags=["auth"])
    def api_me(authorization: str | None = Header(None)):
        """내 정보 조회"""
        user = _get_user(authorization)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "points": user.points,
        }

    # =====================
    # RECIPE ENDPOINTS
    # =====================

    @app.post("/api/recipes", tags=["recipes"])
    def api_create_recipe(
        req: RecipeCreateRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 등록 (포인트 지급)"""
        user = _get_user(authorization)
        recipe = db.create_recipe(
            title=req.title,
            description=req.description,
            instructions=req.instructions,
            author_id=user.id,
            ingredients=[ing.model_dump() for ing in req.ingredients],
            cooking_time_min=req.cooking_time_min,
            servings=req.servings,
            difficulty=req.difficulty,
        )
        updated_user = db.get_user(user.id)
        return {
            "success": True,
            "recipe": _recipe_dict(recipe),
            "points_earned": updated_user.points - user.points,
            "total_points": updated_user.points,
        }

    @app.get("/api/recipes", tags=["recipes"])
    def api_list_recipes(
        offset: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        sort: str = Query("recent", pattern="^(recent|popular|cooking_time)$"),
    ):
        """레시피 목록 조회"""
        recipes = db.list_recipes(offset=offset, limit=limit, sort_by=sort)
        return {
            "recipes": [_recipe_dict(r) for r in recipes],
            "count": len(recipes),
        }

    @app.get("/api/recipes/{recipe_id}", tags=["recipes"])
    def api_get_recipe(
        recipe_id: int,
        authorization: str | None = Header(None),
    ):
        """레시피 상세 조회"""
        recipe = db.get_recipe(recipe_id)
        if not recipe:
            raise HTTPException(404, "레시피를 찾을 수 없습니다")
        ingredients = db.get_recipe_ingredients(recipe_id)
        user = _get_optional_user(authorization)
        liked = db.is_liked(user.id, recipe_id) if user else False
        my_rating = db.get_user_rating(recipe_id, user.id) if user else None
        bookmarked = db.is_bookmarked(user.id, recipe_id) if user else False
        return {
            **_recipe_dict(recipe),
            "ingredients": [
                {"name": i.name, "amount": i.amount, "unit": i.unit}
                for i in ingredients
            ],
            "liked_by_me": liked,
            "my_rating": my_rating,
            "bookmarked_by_me": bookmarked,
        }

    @app.delete("/api/recipes/{recipe_id}", tags=["recipes"])
    def api_delete_recipe(
        recipe_id: int,
        authorization: str | None = Header(None),
    ):
        """레시피 삭제 (본인만 가능)"""
        user = _get_user(authorization)
        deleted = db.delete_recipe(recipe_id, user.id)
        if not deleted:
            raise HTTPException(404, "레시피를 찾을 수 없거나 권한이 없습니다")
        return {"success": True}

    @app.get("/api/users/{user_id}/recipes", tags=["recipes"])
    def api_user_recipes(user_id: int):
        """특정 유저의 레시피 목록"""
        recipes = db.get_user_recipes(user_id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # INGREDIENT MATCHING (핵심 기능)
    # =====================

    @app.post("/api/recipes/search-by-ingredients", tags=["ingredients"])
    def api_search_by_ingredients(req: IngredientSearchRequest):
        """냉장고 재료로 만들 수 있는 레시피 검색

        재료 매칭률이 높은 순서로 정렬됩니다.
        예: 재료 3개 중 2개 일치 → 매칭률 67%
        """
        results = db.find_recipes_by_ingredients(
            ingredient_names=req.ingredients,
            min_match_ratio=req.min_match_ratio,
        )
        return {
            "search_ingredients": req.ingredients,
            "results": [
                {
                    "recipe": _recipe_dict(r["recipe"]),
                    "match_ratio": r["match_ratio"],
                    "matched_count": r["matched_count"],
                    "total_ingredients": r["total_ingredients"],
                    "missing_count": r["missing_count"],
                }
                for r in results
            ],
            "total_found": len(results),
        }

    # =====================
    # COMMENTS
    # =====================

    @app.post("/api/recipes/{recipe_id}/comments", tags=["comments"])
    def api_add_comment(
        recipe_id: int,
        req: CommentCreateRequest,
        authorization: str | None = Header(None),
    ):
        """댓글 작성 (포인트 지급)"""
        user = _get_user(authorization)
        try:
            comment = db.add_comment(recipe_id, user.id, req.content)
            updated_user = db.get_user(user.id)
            return {
                "success": True,
                "comment": _comment_dict(comment),
                "points_earned": 3,
                "total_points": updated_user.points,
            }
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/comments", tags=["comments"])
    def api_get_comments(
        recipe_id: int,
        offset: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
    ):
        """레시피 댓글 목록 조회"""
        comments = db.get_comments(recipe_id, offset=offset, limit=limit)
        return {
            "comments": [_comment_dict(c) for c in comments],
            "count": len(comments),
        }

    @app.put("/api/comments/{comment_id}", tags=["comments"])
    def api_update_comment(
        comment_id: int,
        req: CommentUpdateRequest,
        authorization: str | None = Header(None),
    ):
        """댓글 수정 (본인만 가능)"""
        user = _get_user(authorization)
        try:
            comment = db.update_comment(comment_id, user.id, req.content)
        except ValueError as e:
            raise HTTPException(400, str(e))
        if not comment:
            raise HTTPException(404, "댓글을 찾을 수 없거나 권한이 없습니다")
        return {"success": True, "comment": _comment_dict(comment)}

    @app.delete("/api/comments/{comment_id}", tags=["comments"])
    def api_delete_comment(
        comment_id: int,
        authorization: str | None = Header(None),
    ):
        """댓글 삭제 (본인만 가능)"""
        user = _get_user(authorization)
        deleted = db.delete_comment(comment_id, user.id)
        if not deleted:
            raise HTTPException(404, "댓글을 찾을 수 없거나 권한이 없습니다")
        return {"success": True}

    # =====================
    # RATINGS
    # =====================

    @app.post("/api/recipes/{recipe_id}/rate", tags=["ratings"])
    def api_rate_recipe(
        recipe_id: int,
        req: RatingRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 별점 평가 (1~5). 이미 평가했으면 수정됨. 첫 평가 시 +1 포인트."""
        user = _get_user(authorization)
        try:
            result = db.rate_recipe(recipe_id, user.id, req.score)
            return {"success": True, **result}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/ratings", tags=["ratings"])
    def api_get_ratings(recipe_id: int):
        """레시피 별점 분포 조회"""
        return db.get_recipe_ratings(recipe_id)

    # =====================
    # BOOKMARKS
    # =====================

    @app.post("/api/recipes/{recipe_id}/bookmark", tags=["bookmarks"])
    def api_toggle_bookmark(
        recipe_id: int,
        authorization: str | None = Header(None),
    ):
        """레시피 북마크 토글 (북마크 → 해제, 해제 → 북마크)"""
        user = _get_user(authorization)
        try:
            result = db.toggle_bookmark(user.id, recipe_id)
            return {"success": True, **result}
        except ValueError as e:
            raise HTTPException(404, str(e))

    @app.get("/api/users/{user_id}/bookmarks", tags=["bookmarks"])
    def api_user_bookmarks(user_id: int):
        """유저가 북마크한 레시피 목록"""
        recipes = db.get_user_bookmarks(user_id)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    # =====================
    # LIKE / UNLIKE
    # =====================

    @app.post("/api/recipes/{recipe_id}/like", tags=["likes"])
    def api_toggle_like(
        recipe_id: int,
        authorization: str | None = Header(None),
    ):
        """레시피 좋아요 토글 (좋아요 → 취소, 취소 → 좋아요)

        레시피 작성자에게 좋아요 포인트 지급 (자기 레시피 제외)
        """
        user = _get_user(authorization)
        try:
            result = db.toggle_like(user.id, recipe_id)
            return {"success": True, **result}
        except ValueError as e:
            raise HTTPException(404, str(e))

    @app.get("/api/users/{user_id}/likes", tags=["likes"])
    def api_user_likes(user_id: int):
        """유저가 좋아요한 레시피 목록"""
        recipes = db.get_user_likes(user_id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # POINTS / LEADERBOARD
    # =====================

    @app.get("/api/points/history", tags=["points"])
    def api_point_history(authorization: str | None = Header(None)):
        """내 포인트 내역"""
        user = _get_user(authorization)
        history = db.get_point_history(user.id)
        return {
            "total_points": user.points,
            "history": [
                {
                    "amount": h.amount,
                    "reason": h.reason,
                    "created_at": h.created_at,
                }
                for h in history
            ],
        }

    @app.get("/api/leaderboard", tags=["points"])
    def api_leaderboard(limit: int = Query(20, ge=1, le=100)):
        """포인트 리더보드"""
        users = db.get_leaderboard(limit)
        return {
            "leaderboard": [
                {
                    "rank": i + 1,
                    "username": u.username,
                    "points": u.points,
                }
                for i, u in enumerate(users)
            ],
        }

    # =====================
    # HEALTH
    # =====================

    @app.get("/api/health", tags=["system"])
    def api_health():
        return {"status": "ok", "service": "FridgeChef", "version": "1.0.0"}

    # --- helpers ---

    def _recipe_dict(recipe) -> dict:
        return {
            "id": recipe.id,
            "title": recipe.title,
            "description": recipe.description,
            "instructions": recipe.instructions,
            "author_id": recipe.author_id,
            "author_name": recipe.author_name,
            "cooking_time_min": recipe.cooking_time_min,
            "servings": recipe.servings,
            "difficulty": recipe.difficulty,
            "like_count": recipe.like_count,
            "comment_count": recipe.comment_count,
            "rating_avg": recipe.rating_avg,
            "rating_count": recipe.rating_count,
            "bookmark_count": recipe.bookmark_count,
            "created_at": recipe.created_at,
        }

    def _comment_dict(comment) -> dict:
        return {
            "id": comment.id,
            "recipe_id": comment.recipe_id,
            "user_id": comment.user_id,
            "username": comment.username,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        }

    return app


def _create_simple_app():
    """Fallback app when FastAPI is not installed - uses built-in http server."""
    import http.server
    import urllib.parse

    db = get_db()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path == "/api/health":
                self._json_response({"status": "ok", "service": "FridgeChef"})
            elif path == "/api/recipes":
                recipes = db.list_recipes()
                self._json_response({
                    "recipes": [{"id": r.id, "title": r.title, "like_count": r.like_count} for r in recipes]
                })
            elif path == "/api/leaderboard":
                users = db.get_leaderboard()
                self._json_response({
                    "leaderboard": [{"rank": i+1, "username": u.username, "points": u.points} for i, u in enumerate(users)]
                })
            else:
                self._json_response({"error": "Not found"}, 404)

        def do_POST(self):
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len)) if content_len > 0 else {}
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path == "/api/auth/register":
                try:
                    result = register_user(db, body["username"], body["email"], body["password"])
                    self._json_response({"success": True, **result})
                except (ValueError, KeyError) as e:
                    self._json_response({"error": str(e)}, 400)
            elif path == "/api/auth/login":
                try:
                    result = login_user(db, body["username"], body["password"])
                    self._json_response({"success": True, **result})
                except (ValueError, KeyError) as e:
                    self._json_response({"error": str(e)}, 401)
            elif path == "/api/recipes/search-by-ingredients":
                ingredients = body.get("ingredients", [])
                results = db.find_recipes_by_ingredients(ingredients, body.get("min_match_ratio", 0.3))
                self._json_response({
                    "search_ingredients": ingredients,
                    "results": [
                        {"recipe": {"id": r["recipe"].id, "title": r["recipe"].title},
                         "match_ratio": r["match_ratio"]}
                        for r in results
                    ],
                    "total_found": len(results),
                })
            else:
                self._json_response({"error": "Not found"}, 404)

        def _json_response(self, data: dict, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

        def log_message(self, format, *args):
            pass  # Suppress default logging

    return Handler


# Entry point
if __name__ == "__main__":
    app = create_app()
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        import http.server
        print("FastAPI/uvicorn not found. Starting simple HTTP server on :8000")
        server = http.server.HTTPServer(("0.0.0.0", 8000), app)
        server.serve_forever()
