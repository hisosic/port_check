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

    class TagsRequest(BaseModel):
        tags: list[str] = Field(min_length=1, max_length=20)

    class SearchRequest(BaseModel):
        query: str = Field(min_length=1, max_length=200)

    class ReportRequest(BaseModel):
        target_type: str = Field(pattern="^(recipe|comment)$")
        target_id: int
        reason: str = Field(min_length=1, max_length=1000)

    class ForkRequest(BaseModel):
        title: str | None = None

    class CookLogRequest(BaseModel):
        note: str = ""
        photo_url: str = ""

    class CollectionCreateRequest(BaseModel):
        name: str = Field(min_length=1, max_length=100)
        description: str = ""

    class CollectionAddRequest(BaseModel):
        recipe_id: int

    class MarkReadRequest(BaseModel):
        notification_ids: list[int] | None = None

    class ReplyCreateRequest(BaseModel):
        content: str = Field(min_length=1, max_length=2000)

    class ProfileUpdateRequest(BaseModel):
        bio: str = Field(default="", max_length=500)
        avatar_url: str = ""
        website: str = ""

    class RecipeImageRequest(BaseModel):
        image_url: str = Field(min_length=1)
        caption: str = ""
        sort_order: int = 0

    class NutritionRequest(BaseModel):
        calories: int = Field(ge=0, default=0)
        protein_g: float = Field(ge=0, default=0.0)
        carbs_g: float = Field(ge=0, default=0.0)
        fat_g: float = Field(ge=0, default=0.0)
        fiber_g: float = Field(ge=0, default=0.0)
        sodium_mg: float = Field(ge=0, default=0.0)

    class StepInput(BaseModel):
        title: str = ""
        description: str = Field(min_length=1)
        image_url: str = ""
        timer_minutes: int = Field(ge=0, default=0)

    class RecipeStepsRequest(BaseModel):
        steps: list[StepInput] = Field(min_length=1)

    class IngredientPriceRequest(BaseModel):
        name: str = Field(min_length=1)
        price: float = Field(ge=0)
        unit: str = ""

    class TimerInput(BaseModel):
        label: str = Field(min_length=1)
        duration_seconds: int = Field(gt=0)

    class TimersRequest(BaseModel):
        timers: list[TimerInput] = Field(min_length=1)

    class MealPlanRequest(BaseModel):
        date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
        meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
        recipe_id: int
        note: str = ""

    class ShoppingItemRequest(BaseModel):
        name: str = Field(min_length=1)
        amount: str = ""
        unit: str = ""

    class QAQuestionRequest(BaseModel):
        question: str = Field(min_length=1, max_length=1000)

    class QAAnswerRequest(BaseModel):
        answer: str = Field(min_length=1, max_length=2000)

    class AllergensRequest(BaseModel):
        allergens: list[str] = Field(min_length=1)

    class DifficultyVoteRequest(BaseModel):
        vote: str = Field(pattern="^(easy|medium|hard)$")

    class SubstitutionRequest(BaseModel):
        original: str = Field(min_length=1)
        substitute: str = Field(min_length=1)
        note: str = ""

    class ChallengeCreateRequest(BaseModel):
        title: str = Field(min_length=1)
        description: str = ""
        ingredient: str = ""
        start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
        end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

    class ChallengeEntryRequest(BaseModel):
        recipe_id: int

    class PollCreateRequest(BaseModel):
        question: str = Field(min_length=1)
        options: list[str] = Field(min_length=2, max_length=10)

    class PollVoteRequest(BaseModel):
        option_id: int

    class TipRequest(BaseModel):
        content: str = Field(min_length=1, max_length=1000)

    class SeasonRequest(BaseModel):
        season: str = Field(pattern="^(spring|summer|fall|winter|all)$")

    class BookmarkTagRequest(BaseModel):
        name: str = Field(min_length=1, max_length=50)

    class BookmarkTagAssignRequest(BaseModel):
        recipe_id: int
        tag_id: int

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

    # --- Search & Weekly Popular must be before {recipe_id} to avoid route conflict ---

    @app.get("/api/recipes/search", tags=["search"])
    def api_search_recipes_early(
        q: str = Query(..., min_length=1, max_length=200),
        limit: int = Query(50, ge=1, le=100),
    ):
        """레시피 텍스트 검색 (제목, 설명)"""
        recipes = db.search_recipes(q, limit=limit)
        return {"query": q, "recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.get("/api/recipes/weekly-popular", tags=["recipes"])
    def api_weekly_popular_early(limit: int = Query(20, ge=1, le=100)):
        """주간 인기 레시피"""
        recipes = db.get_weekly_popular(limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.get("/api/recipes/filter", tags=["recipes"])
    def api_filter_recipes(
        difficulty: str | None = Query(None, pattern="^(easy|medium|hard)$"),
        max_time: int | None = Query(None, ge=0),
        min_rating: float | None = Query(None, ge=0, le=5),
        tag: str | None = Query(None),
        sort: str = Query("recent", pattern="^(recent|popular|rating|cooking_time|most_cooked|most_forked)$"),
        offset: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
    ):
        """고급 레시피 필터 (난이도, 시간, 평점, 태그, 정렬)"""
        recipes = db.filter_recipes(
            difficulty=difficulty, max_time=max_time, min_rating=min_rating,
            tag=tag, sort_by=sort, offset=offset, limit=limit,
        )
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.get("/api/recipes/compare", tags=["compare"])
    def api_compare_early(a: int = Query(...), b: int = Query(...)):
        """두 레시피 비교"""
        try:
            return db.compare_recipes(a, b)
        except ValueError as e:
            raise HTTPException(404, str(e))

    @app.get("/api/recipes/allergy-free", tags=["allergy"])
    def api_allergy_free_early(exclude: str = Query(...), limit: int = Query(50, ge=1, le=100)):
        """특정 알레르기 제외 레시피"""
        allergens = [a.strip() for a in exclude.split(",") if a.strip()]
        recipes = db.find_recipes_without_allergens(allergens, limit=limit)
        return {"excluded": allergens, "recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.get("/api/recipes/seasonal/{season}", tags=["season"])
    def api_seasonal_early(season: str, limit: int = Query(50, ge=1, le=100)):
        """계절별 레시피"""
        recipes = db.get_seasonal_recipes(season, limit=limit)
        return {"season": season, "recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

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
        tags = db.get_recipe_tags(recipe_id)
        return {
            **_recipe_dict(recipe),
            "ingredients": [
                {"name": i.name, "amount": i.amount, "unit": i.unit}
                for i in ingredients
            ],
            "tags": tags,
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
    # FOLLOW (Feature 1)
    # =====================

    @app.post("/api/users/{user_id}/follow", tags=["follow"])
    def api_toggle_follow(
        user_id: int,
        authorization: str | None = Header(None),
    ):
        """유저 팔로우/언팔로우 토글"""
        me = _get_user(authorization)
        try:
            result = db.toggle_follow(me.id, user_id)
            return {"success": True, **result}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/users/{user_id}/followers", tags=["follow"])
    def api_get_followers(user_id: int):
        """유저의 팔로워 목록"""
        followers = db.get_followers(user_id)
        return {
            "followers": [{"id": u.id, "username": u.username, "points": u.points} for u in followers],
            "count": len(followers),
        }

    @app.get("/api/users/{user_id}/following", tags=["follow"])
    def api_get_following(user_id: int):
        """유저가 팔로우하는 목록"""
        following = db.get_following(user_id)
        return {
            "following": [{"id": u.id, "username": u.username, "points": u.points} for u in following],
            "count": len(following),
        }

    @app.get("/api/feed", tags=["follow"])
    def api_feed(
        limit: int = Query(50, ge=1, le=100),
        authorization: str | None = Header(None),
    ):
        """팔로우한 유저들의 최신 레시피 피드"""
        user = _get_user(authorization)
        recipes = db.get_following_recipes(user.id, limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    # =====================
    # TAGS (Feature 2)
    # =====================

    @app.put("/api/recipes/{recipe_id}/tags", tags=["tags"])
    def api_set_tags(
        recipe_id: int,
        req: TagsRequest,
        authorization: str | None = Header(None),
    ):
        """레시피에 태그 설정 (본인만 가능)"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        tags = db.set_recipe_tags(recipe_id, req.tags)
        return {"success": True, "tags": tags}

    @app.get("/api/recipes/{recipe_id}/tags", tags=["tags"])
    def api_get_tags(recipe_id: int):
        """레시피 태그 조회"""
        return {"tags": db.get_recipe_tags(recipe_id)}

    @app.get("/api/tags/{tag_name}/recipes", tags=["tags"])
    def api_recipes_by_tag(tag_name: str, limit: int = Query(50, ge=1, le=100)):
        """태그별 레시피 검색"""
        recipes = db.find_recipes_by_tag(tag_name, limit=limit)
        return {"tag": tag_name, "recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.get("/api/tags/popular", tags=["tags"])
    def api_popular_tags(limit: int = Query(20, ge=1, le=100)):
        """인기 태그 목록"""
        return {"tags": db.get_popular_tags(limit=limit)}

    # =====================
    # REPORT (Feature 4)
    # =====================

    @app.post("/api/reports", tags=["reports"])
    def api_create_report(
        req: ReportRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 또는 댓글 신고"""
        user = _get_user(authorization)
        try:
            report = db.create_report(user.id, req.target_type, req.target_id, req.reason)
            return {
                "success": True,
                "report": {
                    "id": report.id,
                    "target_type": report.target_type,
                    "target_id": report.target_id,
                    "status": report.status,
                },
            }
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/reports", tags=["reports"])
    def api_get_reports(
        status: str = Query("pending", pattern="^(pending|reviewed|dismissed)$"),
        limit: int = Query(50, ge=1, le=100),
    ):
        """신고 목록 조회 (관리용)"""
        reports = db.get_reports(status=status, limit=limit)
        return {
            "reports": [
                {"id": r.id, "reporter_id": r.reporter_id, "target_type": r.target_type,
                 "target_id": r.target_id, "reason": r.reason, "status": r.status,
                 "created_at": r.created_at}
                for r in reports
            ],
            "count": len(reports),
        }

    # =====================
    # FORK (Feature 5)
    # =====================

    @app.post("/api/recipes/{recipe_id}/fork", tags=["fork"])
    def api_fork_recipe(
        recipe_id: int,
        req: ForkRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 포크(리믹스) — 다른 유저의 레시피를 기반으로 내 버전 생성"""
        user = _get_user(authorization)
        try:
            forked = db.fork_recipe(recipe_id, user.id, title=req.title)
            updated_user = db.get_user(user.id)
            return {
                "success": True,
                "recipe": _recipe_dict(forked),
                "forked_from": recipe_id,
                "total_points": updated_user.points,
            }
        except ValueError as e:
            raise HTTPException(400, str(e))

    # =====================
    # COOK LOG (Feature 7)
    # =====================

    @app.post("/api/recipes/{recipe_id}/cook-log", tags=["cook_log"])
    def api_add_cook_log(
        recipe_id: int,
        req: CookLogRequest,
        authorization: str | None = Header(None),
    ):
        """요리 완료 기록 (+2 포인트)"""
        user = _get_user(authorization)
        try:
            log = db.add_cook_log(user.id, recipe_id, note=req.note, photo_url=req.photo_url)
            updated_user = db.get_user(user.id)
            return {
                "success": True,
                "cook_log": {"id": log.id, "recipe_id": log.recipe_id,
                             "note": log.note, "created_at": log.created_at},
                "points_earned": 2,
                "total_points": updated_user.points,
            }
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/cook-logs", tags=["cook_log"])
    def api_get_cook_logs(recipe_id: int, limit: int = Query(50, ge=1, le=100)):
        """레시피의 요리 기록 목록"""
        logs = db.get_cook_logs(recipe_id, limit=limit)
        return {
            "cook_logs": [
                {"id": cl.id, "user_id": cl.user_id, "username": cl.username,
                 "note": cl.note, "photo_url": cl.photo_url, "created_at": cl.created_at}
                for cl in logs
            ],
            "count": len(logs),
        }

    @app.get("/api/users/{user_id}/cook-logs", tags=["cook_log"])
    def api_user_cook_logs(user_id: int, limit: int = Query(50, ge=1, le=100)):
        """유저의 요리 기록"""
        logs = db.get_user_cook_logs(user_id, limit=limit)
        return {
            "cook_logs": [
                {"id": cl.id, "recipe_id": cl.recipe_id, "note": cl.note,
                 "photo_url": cl.photo_url, "created_at": cl.created_at}
                for cl in logs
            ],
            "count": len(logs),
        }

    # =====================
    # COLLECTIONS (Feature 8)
    # =====================

    @app.post("/api/collections", tags=["collections"])
    def api_create_collection(
        req: CollectionCreateRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 컬렉션 생성"""
        user = _get_user(authorization)
        try:
            coll = db.create_collection(user.id, req.name, req.description)
            return {"success": True, "collection": {"id": coll.id, "name": coll.name, "description": coll.description}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/users/{user_id}/collections", tags=["collections"])
    def api_user_collections(user_id: int):
        """유저의 컬렉션 목록"""
        colls = db.get_user_collections(user_id)
        return {
            "collections": [
                {"id": c.id, "name": c.name, "description": c.description, "created_at": c.created_at}
                for c in colls
            ],
        }

    @app.delete("/api/collections/{collection_id}", tags=["collections"])
    def api_delete_collection(
        collection_id: int,
        authorization: str | None = Header(None),
    ):
        """컬렉션 삭제 (본인만)"""
        user = _get_user(authorization)
        deleted = db.delete_collection(collection_id, user.id)
        if not deleted:
            raise HTTPException(404, "컬렉션을 찾을 수 없거나 권한이 없습니다")
        return {"success": True}

    @app.post("/api/collections/{collection_id}/recipes", tags=["collections"])
    def api_add_to_collection(
        collection_id: int,
        req: CollectionAddRequest,
        authorization: str | None = Header(None),
    ):
        """컬렉션에 레시피 추가"""
        user = _get_user(authorization)
        try:
            db.add_to_collection(collection_id, req.recipe_id, user.id)
            return {"success": True}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.delete("/api/collections/{collection_id}/recipes/{recipe_id}", tags=["collections"])
    def api_remove_from_collection(
        collection_id: int,
        recipe_id: int,
        authorization: str | None = Header(None),
    ):
        """컬렉션에서 레시피 제거"""
        user = _get_user(authorization)
        removed = db.remove_from_collection(collection_id, recipe_id, user.id)
        if not removed:
            raise HTTPException(404, "컬렉션에서 레시피를 찾을 수 없습니다")
        return {"success": True}

    @app.get("/api/collections/{collection_id}/recipes", tags=["collections"])
    def api_collection_recipes(collection_id: int):
        """컬렉션의 레시피 목록"""
        recipes = db.get_collection_recipes(collection_id)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    # =====================
    # NOTIFICATIONS (Feature 9)
    # =====================

    @app.get("/api/notifications", tags=["notifications"])
    def api_get_notifications(
        unread_only: bool = Query(False),
        limit: int = Query(50, ge=1, le=100),
        authorization: str | None = Header(None),
    ):
        """내 알림 목록"""
        user = _get_user(authorization)
        notifs = db.get_notifications(user.id, unread_only=unread_only, limit=limit)
        return {
            "notifications": [
                {"id": n.id, "type": n.type, "message": n.message,
                 "reference_id": n.reference_id, "is_read": n.is_read,
                 "created_at": n.created_at}
                for n in notifs
            ],
            "unread_count": db.get_unread_count(user.id),
        }

    @app.post("/api/notifications/read", tags=["notifications"])
    def api_mark_read(
        req: MarkReadRequest,
        authorization: str | None = Header(None),
    ):
        """알림 읽음 처리 (ids 미지정 시 전체 읽음)"""
        user = _get_user(authorization)
        count = db.mark_notifications_read(user.id, req.notification_ids)
        return {"success": True, "marked_count": count}

    @app.get("/api/notifications/unread-count", tags=["notifications"])
    def api_unread_count(authorization: str | None = Header(None)):
        """읽지 않은 알림 수"""
        user = _get_user(authorization)
        return {"unread_count": db.get_unread_count(user.id)}

    # =====================
    # SHARE LINK (Feature 10)
    # =====================

    @app.post("/api/recipes/{recipe_id}/share", tags=["share"])
    def api_create_share_link(recipe_id: int):
        """레시피 공유 링크 생성"""
        try:
            link = db.create_share_link(recipe_id)
            return {"success": True, "token": link.token, "view_count": link.view_count}
        except ValueError as e:
            raise HTTPException(404, str(e))

    @app.get("/api/shared/{token}", tags=["share"])
    def api_get_shared_recipe(token: str):
        """공유 링크로 레시피 조회 (조회수 +1)"""
        recipe = db.get_recipe_by_share_token(token)
        if not recipe:
            raise HTTPException(404, "공유 링크를 찾을 수 없습니다")
        ingredients = db.get_recipe_ingredients(recipe.id)
        tags = db.get_recipe_tags(recipe.id)
        return {
            **_recipe_dict(recipe),
            "ingredients": [
                {"name": i.name, "amount": i.amount, "unit": i.unit}
                for i in ingredients
            ],
            "tags": tags,
        }

    # =====================
    # REPLIES (Feature 11)
    # =====================

    @app.post("/api/comments/{comment_id}/replies", tags=["comments"])
    def api_add_reply(
        comment_id: int,
        req: ReplyCreateRequest,
        authorization: str | None = Header(None),
    ):
        """댓글에 답글 작성 (+1 포인트)"""
        user = _get_user(authorization)
        try:
            reply = db.add_reply(comment_id, user.id, req.content)
            return {"success": True, "reply": _comment_dict(reply), "points_earned": 1}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/comments/{comment_id}/replies", tags=["comments"])
    def api_get_replies(comment_id: int):
        """댓글의 답글 목록"""
        replies = db.get_replies(comment_id)
        return {"replies": [_comment_dict(r) for r in replies], "count": len(replies)}

    # =====================
    # USER PROFILE (Feature 12)
    # =====================

    @app.put("/api/profile", tags=["profile"])
    def api_update_profile(
        req: ProfileUpdateRequest,
        authorization: str | None = Header(None),
    ):
        """내 프로필 수정"""
        user = _get_user(authorization)
        profile = db.update_profile(user.id, bio=req.bio, avatar_url=req.avatar_url, website=req.website)
        return {"success": True, "profile": {"bio": profile.bio, "avatar_url": profile.avatar_url, "website": profile.website}}

    @app.get("/api/users/{user_id}/profile", tags=["profile"])
    def api_get_user_detail(user_id: int):
        """유저 상세 프로필 조회 (배지, 팔로워 수 포함)"""
        detail = db.get_user_detail(user_id)
        if not detail:
            raise HTTPException(404, "유저를 찾을 수 없습니다")
        return detail

    # =====================
    # RECIPE IMAGES (Feature 13)
    # =====================

    @app.post("/api/recipes/{recipe_id}/images", tags=["images"])
    def api_add_image(
        recipe_id: int,
        req: RecipeImageRequest,
        authorization: str | None = Header(None),
    ):
        """레시피에 이미지 추가 (본인만)"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        try:
            img = db.add_recipe_image(recipe_id, req.image_url, req.caption, req.sort_order)
            return {"success": True, "image": {"id": img.id, "image_url": img.image_url, "caption": img.caption}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/images", tags=["images"])
    def api_get_images(recipe_id: int):
        """레시피 이미지 목록"""
        images = db.get_recipe_images(recipe_id)
        return {"images": [{"id": i.id, "image_url": i.image_url, "caption": i.caption, "sort_order": i.sort_order} for i in images]}

    @app.delete("/api/images/{image_id}", tags=["images"])
    def api_delete_image(image_id: int, authorization: str | None = Header(None)):
        """이미지 삭제 (레시피 작성자만)"""
        user = _get_user(authorization)
        if not db.delete_recipe_image(image_id, user.id):
            raise HTTPException(404, "이미지를 찾을 수 없거나 권한이 없습니다")
        return {"success": True}

    # =====================
    # NUTRITION (Feature 14)
    # =====================

    @app.put("/api/recipes/{recipe_id}/nutrition", tags=["nutrition"])
    def api_set_nutrition(
        recipe_id: int,
        req: NutritionRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 영양 정보 설정 (본인만)"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        info = db.set_nutrition(recipe_id, calories=req.calories, protein_g=req.protein_g,
                                carbs_g=req.carbs_g, fat_g=req.fat_g,
                                fiber_g=req.fiber_g, sodium_mg=req.sodium_mg)
        return {"success": True, "nutrition": {
            "calories": info.calories, "protein_g": info.protein_g, "carbs_g": info.carbs_g,
            "fat_g": info.fat_g, "fiber_g": info.fiber_g, "sodium_mg": info.sodium_mg,
        }}

    @app.get("/api/recipes/{recipe_id}/nutrition", tags=["nutrition"])
    def api_get_nutrition(recipe_id: int):
        """레시피 영양 정보 조회"""
        info = db.get_nutrition(recipe_id)
        if not info:
            return {"nutrition": None}
        return {"nutrition": {
            "calories": info.calories, "protein_g": info.protein_g, "carbs_g": info.carbs_g,
            "fat_g": info.fat_g, "fiber_g": info.fiber_g, "sodium_mg": info.sodium_mg,
        }}

    # =====================
    # RECIPE STEPS (Feature 15)
    # =====================

    @app.put("/api/recipes/{recipe_id}/steps", tags=["steps"])
    def api_set_steps(
        recipe_id: int,
        req: RecipeStepsRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 조리 단계 설정 (본인만)"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        steps = db.set_recipe_steps(recipe_id, [s.model_dump() for s in req.steps])
        return {"success": True, "steps": [
            {"step_number": s.step_number, "title": s.title, "description": s.description,
             "image_url": s.image_url, "timer_minutes": s.timer_minutes}
            for s in steps
        ]}

    @app.get("/api/recipes/{recipe_id}/steps", tags=["steps"])
    def api_get_steps(recipe_id: int):
        """레시피 조리 단계 조회"""
        steps = db.get_recipe_steps(recipe_id)
        return {"steps": [
            {"step_number": s.step_number, "title": s.title, "description": s.description,
             "image_url": s.image_url, "timer_minutes": s.timer_minutes}
            for s in steps
        ]}

    # =====================
    # INGREDIENT PRICES (Feature 16)
    # =====================

    @app.post("/api/ingredient-prices", tags=["prices"])
    def api_set_price(req: IngredientPriceRequest):
        """식재료 가격 등록/수정"""
        try:
            p = db.set_ingredient_price(req.name, req.price, req.unit)
            return {"success": True, "ingredient": {"name": p.name, "price": p.price, "unit": p.unit}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/cost", tags=["prices"])
    def api_estimate_cost(recipe_id: int):
        """레시피 예상 비용 산출"""
        return db.estimate_recipe_cost(recipe_id)

    # =====================
    # BADGES (Feature 17)
    # =====================

    @app.get("/api/badges", tags=["badges"])
    def api_all_badges():
        """전체 배지 목록"""
        badges = db.get_all_badges()
        return {"badges": [{"code": b.code, "name": b.name, "description": b.description, "icon": b.icon} for b in badges]}

    @app.get("/api/users/{user_id}/badges", tags=["badges"])
    def api_user_badges(user_id: int):
        """유저 획득 배지 목록"""
        badges = db.get_user_badges(user_id)
        return {"badges": [{"code": b.badge_code, "name": b.badge_name, "earned_at": b.earned_at} for b in badges]}

    @app.post("/api/badges/check", tags=["badges"])
    def api_check_badges(authorization: str | None = Header(None)):
        """내 배지 조건 확인 및 자동 수여"""
        user = _get_user(authorization)
        awarded = db.check_and_award_badges(user.id)
        return {"newly_awarded": awarded, "total_badges": len(db.get_user_badges(user.id))}

    # =====================
    # RECOMMENDATIONS (Feature 18)
    # =====================

    @app.get("/api/recipes/{recipe_id}/similar", tags=["recommendations"])
    def api_similar_recipes(recipe_id: int, limit: int = Query(10, ge=1, le=50)):
        """비슷한 레시피 추천 (재료 기반)"""
        recipes = db.get_similar_recipes(recipe_id, limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    # =====================
    # COOKING TIMERS (Feature 20)
    # =====================

    @app.put("/api/recipes/{recipe_id}/timers", tags=["timers"])
    def api_set_timers(
        recipe_id: int,
        req: TimersRequest,
        authorization: str | None = Header(None),
    ):
        """레시피 쿠킹 타이머 설정 (본인만)"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        timers = db.set_cooking_timers(recipe_id, [t.model_dump() for t in req.timers])
        return {"success": True, "timers": [
            {"label": t.label, "duration_seconds": t.duration_seconds, "sort_order": t.sort_order}
            for t in timers
        ]}

    @app.get("/api/recipes/{recipe_id}/timers", tags=["timers"])
    def api_get_timers(recipe_id: int):
        """레시피 쿠킹 타이머 조회"""
        timers = db.get_cooking_timers(recipe_id)
        return {"timers": [
            {"label": t.label, "duration_seconds": t.duration_seconds, "sort_order": t.sort_order}
            for t in timers
        ]}

    # =====================
    # MEAL PLANNER (Feature 21)
    # =====================

    @app.post("/api/meal-plans", tags=["meal_plan"])
    def api_set_meal_plan(req: MealPlanRequest, authorization: str | None = Header(None)):
        """식단 계획 설정"""
        user = _get_user(authorization)
        try:
            plan = db.set_meal_plan(user.id, req.date, req.meal_type, req.recipe_id, req.note)
            return {"success": True, "meal_plan": {"date": plan.date, "meal_type": plan.meal_type, "recipe_id": plan.recipe_id}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/meal-plans", tags=["meal_plan"])
    def api_get_meal_plans(
        start: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
        end: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
        authorization: str | None = Header(None),
    ):
        """기간별 식단 계획 조회"""
        user = _get_user(authorization)
        plans = db.get_meal_plans(user.id, start, end)
        return {"meal_plans": [{"date": p.date, "meal_type": p.meal_type, "recipe_id": p.recipe_id, "note": p.note} for p in plans]}

    @app.delete("/api/meal-plans", tags=["meal_plan"])
    def api_delete_meal_plan(
        date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
        meal_type: str = Query(..., pattern="^(breakfast|lunch|dinner|snack)$"),
        authorization: str | None = Header(None),
    ):
        """식단 계획 삭제"""
        user = _get_user(authorization)
        db.delete_meal_plan(user.id, date, meal_type)
        return {"success": True}

    # =====================
    # SHOPPING LIST (Feature 22)
    # =====================

    @app.post("/api/shopping-list", tags=["shopping"])
    def api_add_shopping_item(req: ShoppingItemRequest, authorization: str | None = Header(None)):
        """장바구니에 항목 추가"""
        user = _get_user(authorization)
        item = db.add_shopping_item(user.id, req.name, req.amount, req.unit)
        return {"success": True, "item": {"id": item.id, "name": item.name}}

    @app.post("/api/shopping-list/from-recipe/{recipe_id}", tags=["shopping"])
    def api_add_recipe_to_shopping(recipe_id: int, authorization: str | None = Header(None)):
        """레시피 재료를 장바구니에 일괄 추가"""
        user = _get_user(authorization)
        try:
            items = db.add_recipe_to_shopping(user.id, recipe_id)
            return {"success": True, "added_count": len(items)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/shopping-list", tags=["shopping"])
    def api_get_shopping_list(authorization: str | None = Header(None)):
        """내 장바구니 목록"""
        user = _get_user(authorization)
        items = db.get_shopping_list(user.id)
        return {"items": [{"id": i.id, "name": i.name, "amount": i.amount, "unit": i.unit, "checked": i.checked} for i in items]}

    @app.post("/api/shopping-list/{item_id}/toggle", tags=["shopping"])
    def api_toggle_shopping(item_id: int, authorization: str | None = Header(None)):
        """장바구니 항목 체크/해제"""
        user = _get_user(authorization)
        db.toggle_shopping_item(item_id, user.id)
        return {"success": True}

    @app.delete("/api/shopping-list/{item_id}", tags=["shopping"])
    def api_delete_shopping_item(item_id: int, authorization: str | None = Header(None)):
        """장바구니 항목 삭제"""
        user = _get_user(authorization)
        db.delete_shopping_item(item_id, user.id)
        return {"success": True}

    @app.delete("/api/shopping-list", tags=["shopping"])
    def api_clear_shopping(checked_only: bool = Query(False), authorization: str | None = Header(None)):
        """장바구니 비우기"""
        user = _get_user(authorization)
        count = db.clear_shopping_list(user.id, checked_only=checked_only)
        return {"success": True, "removed_count": count}

    # =====================
    # BLOCK USER (Feature 23)
    # =====================

    @app.post("/api/users/{user_id}/block", tags=["block"])
    def api_block_user(user_id: int, authorization: str | None = Header(None)):
        """유저 차단"""
        me = _get_user(authorization)
        try:
            return {"success": True, **db.block_user(me.id, user_id)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.delete("/api/users/{user_id}/block", tags=["block"])
    def api_unblock_user(user_id: int, authorization: str | None = Header(None)):
        """유저 차단 해제"""
        me = _get_user(authorization)
        db.unblock_user(me.id, user_id)
        return {"success": True}

    @app.get("/api/blocked-users", tags=["block"])
    def api_blocked_users(authorization: str | None = Header(None)):
        """차단 목록"""
        user = _get_user(authorization)
        users = db.get_blocked_users(user.id)
        return {"blocked": [{"id": u.id, "username": u.username} for u in users]}

    # =====================
    # RECIPE Q&A (Feature 24)
    # =====================

    @app.post("/api/recipes/{recipe_id}/qa", tags=["qa"])
    def api_ask_question(recipe_id: int, req: QAQuestionRequest, authorization: str | None = Header(None)):
        """레시피에 질문"""
        user = _get_user(authorization)
        try:
            qa = db.ask_question(recipe_id, user.id, req.question)
            return {"success": True, "qa": {"id": qa.id, "question": qa.question}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/qa/{qa_id}/answer", tags=["qa"])
    def api_answer_question(qa_id: int, req: QAAnswerRequest, authorization: str | None = Header(None)):
        """질문에 답변 (+2 포인트)"""
        user = _get_user(authorization)
        try:
            qa = db.answer_question(qa_id, user.id, req.answer)
            if not qa:
                raise HTTPException(404, "질문을 찾을 수 없습니다")
            return {"success": True, "qa": {"id": qa.id, "answer": qa.answer}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/qa", tags=["qa"])
    def api_get_qa(recipe_id: int):
        """레시피 Q&A 목록"""
        qas = db.get_recipe_qa(recipe_id)
        return {"qa": [{"id": q.id, "question": q.question, "answer": q.answer,
                         "username": q.username, "answered_at": q.answered_at} for q in qas]}

    # =====================
    # SEASONAL RECIPES (Feature 25)
    # =====================

    @app.put("/api/recipes/{recipe_id}/season", tags=["season"])
    def api_set_season(recipe_id: int, req: SeasonRequest, authorization: str | None = Header(None)):
        """레시피 계절 설정"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        db.set_recipe_season(recipe_id, req.season)
        return {"success": True, "season": req.season}

    # =====================
    # ALLERGY INFO (Feature 26)
    # =====================

    @app.put("/api/recipes/{recipe_id}/allergens", tags=["allergy"])
    def api_set_allergens(recipe_id: int, req: AllergensRequest, authorization: str | None = Header(None)):
        """레시피 알레르기 정보 설정"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        allergens = db.set_allergens(recipe_id, req.allergens)
        return {"success": True, "allergens": allergens}

    @app.get("/api/recipes/{recipe_id}/allergens", tags=["allergy"])
    def api_get_allergens(recipe_id: int):
        """레시피 알레르기 정보"""
        return {"allergens": db.get_allergens(recipe_id)}

    # =====================
    # DIFFICULTY VOTE (Feature 27)
    # =====================

    @app.post("/api/recipes/{recipe_id}/difficulty-vote", tags=["difficulty"])
    def api_vote_difficulty(recipe_id: int, req: DifficultyVoteRequest, authorization: str | None = Header(None)):
        """레시피 체감 난이도 투표"""
        user = _get_user(authorization)
        result = db.vote_difficulty(recipe_id, user.id, req.vote)
        return {"success": True, **result}

    @app.get("/api/recipes/{recipe_id}/difficulty-votes", tags=["difficulty"])
    def api_get_difficulty_votes(recipe_id: int):
        """레시피 난이도 투표 현황"""
        return db.get_difficulty_votes(recipe_id)

    # =====================
    # USER STATS (Feature 29)
    # =====================

    @app.get("/api/users/{user_id}/stats", tags=["stats"])
    def api_user_stats(user_id: int):
        """유저 활동 통계 대시보드"""
        return db.get_user_stats(user_id)

    # =====================
    # VIEW HISTORY (Feature 30)
    # =====================

    @app.post("/api/recipes/{recipe_id}/view", tags=["history"])
    def api_record_view(recipe_id: int, authorization: str | None = Header(None)):
        """레시피 조회 기록"""
        user = _get_optional_user(authorization)
        if user:
            db.record_view(user.id, recipe_id)
        return {"success": True}

    @app.get("/api/view-history", tags=["history"])
    def api_view_history(limit: int = Query(50, ge=1, le=100), authorization: str | None = Header(None)):
        """최근 본 레시피"""
        user = _get_user(authorization)
        history = db.get_view_history(user.id, limit=limit)
        return {"history": history}

    # =====================
    # INGREDIENT SUBSTITUTION (Feature 31)
    # =====================

    @app.post("/api/ingredient-subs", tags=["substitution"])
    def api_add_sub(req: SubstitutionRequest):
        """대체 재료 등록"""
        try:
            sub = db.add_substitution(req.original, req.substitute, req.note)
            return {"success": True, "substitution": {"original": sub.original, "substitute": sub.substitute}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/ingredient-subs/{ingredient}", tags=["substitution"])
    def api_get_subs(ingredient: str):
        """재료의 대체 목록"""
        subs = db.get_substitutions(ingredient)
        return {"ingredient": ingredient, "substitutes": [{"substitute": s.substitute, "note": s.note} for s in subs]}

    # =====================
    # COOKING CHALLENGE (Feature 32)
    # =====================

    @app.post("/api/challenges", tags=["challenge"])
    def api_create_challenge(req: ChallengeCreateRequest, authorization: str | None = Header(None)):
        """쿠킹 챌린지 생성"""
        _get_user(authorization)
        try:
            ch = db.create_challenge(req.title, req.description, req.ingredient, req.start_date, req.end_date)
            return {"success": True, "challenge": {"id": ch.id, "title": ch.title}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/challenges/{challenge_id}/enter", tags=["challenge"])
    def api_enter_challenge(challenge_id: int, req: ChallengeEntryRequest, authorization: str | None = Header(None)):
        """챌린지 참여 (+5 포인트)"""
        user = _get_user(authorization)
        try:
            return {"success": True, **db.enter_challenge(challenge_id, user.id, req.recipe_id)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/challenges/{challenge_id}/entries", tags=["challenge"])
    def api_challenge_entries(challenge_id: int):
        """챌린지 참여 목록"""
        return {"entries": db.get_challenge_entries(challenge_id)}

    @app.get("/api/challenges/active", tags=["challenge"])
    def api_active_challenges():
        """진행 중인 챌린지"""
        chs = db.get_active_challenges()
        return {"challenges": [{"id": c.id, "title": c.title, "description": c.description,
                                 "ingredient": c.ingredient, "end_date": c.end_date} for c in chs]}

    # =====================
    # POLLS (Feature 33)
    # =====================

    @app.post("/api/recipes/{recipe_id}/polls", tags=["polls"])
    def api_create_poll(recipe_id: int, req: PollCreateRequest, authorization: str | None = Header(None)):
        """레시피 투표 생성"""
        user = _get_user(authorization)
        try:
            return {"success": True, **db.create_poll(recipe_id, user.id, req.question, req.options)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/polls/{poll_id}/vote", tags=["polls"])
    def api_vote_poll(poll_id: int, req: PollVoteRequest, authorization: str | None = Header(None)):
        """투표하기"""
        user = _get_user(authorization)
        try:
            return {"success": True, **db.vote_poll(poll_id, req.option_id, user.id)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/polls/{poll_id}", tags=["polls"])
    def api_get_poll(poll_id: int):
        """투표 현황 조회"""
        poll = db.get_poll(poll_id)
        if not poll:
            raise HTTPException(404, "투표를 찾을 수 없습니다")
        return poll

    # =====================
    # USER LEVEL (Feature 34)
    # =====================

    @app.get("/api/users/{user_id}/level", tags=["level"])
    def api_user_level(user_id: int):
        """유저 레벨 조회"""
        try:
            return db.get_user_level(user_id)
        except ValueError as e:
            raise HTTPException(404, str(e))

    # =====================
    # RECIPE TIPS (Feature 35)
    # =====================

    @app.post("/api/recipes/{recipe_id}/tips", tags=["tips"])
    def api_add_tip(recipe_id: int, req: TipRequest, authorization: str | None = Header(None)):
        """레시피 꿀팁 작성"""
        user = _get_user(authorization)
        try:
            tip = db.add_recipe_tip(recipe_id, user.id, req.content)
            return {"success": True, "tip": {"id": tip.id, "content": tip.content}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/tips", tags=["tips"])
    def api_get_tips(recipe_id: int):
        """레시피 꿀팁 목록"""
        tips = db.get_recipe_tips(recipe_id)
        return {"tips": [{"id": t.id, "username": t.username, "content": t.content, "created_at": t.created_at} for t in tips]}

    # =====================
    # EXPORT (Feature 36)
    # =====================

    @app.get("/api/recipes/{recipe_id}/export", tags=["export"])
    def api_export_recipe(recipe_id: int, format: str = Query("json", pattern="^(json|text)$")):
        """레시피 내보내기 (JSON/텍스트)"""
        try:
            return {"export": db.export_recipe(recipe_id, format=format)}
        except ValueError as e:
            raise HTTPException(404, str(e))

    # =====================
    # RECIPE VERSIONS (Feature 37)
    # =====================

    @app.post("/api/recipes/{recipe_id}/versions", tags=["versions"])
    def api_save_version(recipe_id: int, authorization: str | None = Header(None)):
        """현재 레시피 상태를 버전으로 저장"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        try:
            ver = db.save_recipe_version(recipe_id)
            return {"success": True, "version": {"version_num": ver.version_num, "title": ver.title}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/versions", tags=["versions"])
    def api_get_versions(recipe_id: int):
        """레시피 버전 이력"""
        versions = db.get_recipe_versions(recipe_id)
        return {"versions": [{"version_num": v.version_num, "title": v.title, "created_at": v.created_at} for v in versions]}

    # =====================
    # BOOKMARK TAGS (Feature 38)
    # =====================

    @app.post("/api/bookmark-tags", tags=["bookmark_tags"])
    def api_create_bookmark_tag(req: BookmarkTagRequest, authorization: str | None = Header(None)):
        """북마크 태그 생성"""
        user = _get_user(authorization)
        try:
            tag = db.create_bookmark_tag(user.id, req.name)
            return {"success": True, "tag": {"id": tag.id, "name": tag.name}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/bookmark-tags", tags=["bookmark_tags"])
    def api_get_bookmark_tags(authorization: str | None = Header(None)):
        """내 북마크 태그 목록"""
        user = _get_user(authorization)
        tags = db.get_bookmark_tags(user.id)
        return {"tags": [{"id": t.id, "name": t.name} for t in tags]}

    @app.post("/api/bookmark-tags/assign", tags=["bookmark_tags"])
    def api_assign_bookmark_tag(req: BookmarkTagAssignRequest, authorization: str | None = Header(None)):
        """북마크에 태그 할당"""
        user = _get_user(authorization)
        try:
            db.tag_bookmark(user.id, req.recipe_id, req.tag_id)
            return {"success": True}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/bookmark-tags/{tag_id}/recipes", tags=["bookmark_tags"])
    def api_bookmarks_by_tag(tag_id: int, authorization: str | None = Header(None)):
        """태그별 북마크 레시피"""
        user = _get_user(authorization)
        recipes = db.get_bookmarks_by_tag(user.id, tag_id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # PRINT FORMAT (Feature 39)
    # =====================

    @app.get("/api/recipes/{recipe_id}/print", tags=["print"])
    def api_print_recipe(recipe_id: int):
        """레시피 인쇄용 포맷"""
        data = db.get_print_format(recipe_id)
        if not data:
            raise HTTPException(404, "레시피를 찾을 수 없습니다")
        return data

    # =====================
    # DUPLICATE DETECTION (Feature 40)
    # =====================

    @app.get("/api/recipes/{recipe_id}/duplicates", tags=["duplicates"])
    def api_find_duplicates(recipe_id: int, threshold: float = Query(0.7, ge=0, le=1)):
        """유사/중복 레시피 탐지"""
        return {"duplicates": db.find_duplicates(recipe_id, threshold=threshold)}

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
            "fork_count": recipe.fork_count,
            "cook_count": recipe.cook_count,
            "view_count": recipe.view_count,
            "season": recipe.season,
            "forked_from_id": recipe.forked_from_id,
            "created_at": recipe.created_at,
        }

    def _comment_dict(comment) -> dict:
        return {
            "id": comment.id,
            "recipe_id": comment.recipe_id,
            "user_id": comment.user_id,
            "username": comment.username,
            "content": comment.content,
            "parent_id": comment.parent_id,
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
