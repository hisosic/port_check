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

    class CategoryRequest(BaseModel):
        category: str = Field(min_length=1, max_length=50)

    class EquipmentRequest(BaseModel):
        equipment: list[str] = Field(min_length=1)

    class UserNoteRequest(BaseModel):
        content: str = Field(min_length=1, max_length=2000)

    class VisibilityRequest(BaseModel):
        is_public: bool

    class ScheduleRequest(BaseModel):
        publish_at: float = Field(gt=0)

    class TranslationRequest(BaseModel):
        language: str = Field(min_length=2, max_length=10)
        title: str = Field(min_length=1)
        description: str = ""

    class PantryItemRequest(BaseModel):
        name: str = Field(min_length=1)
        amount: str = ""
        unit: str = ""
        expiry_date: str = ""

    class NotificationPrefRequest(BaseModel):
        likes: bool = True
        comments: bool = True
        follows: bool = True
        challenges: bool = True

    class AttemptLogRequest(BaseModel):
        status: str = Field(pattern="^(success|failed|partial)$")
        note: str = ""

    class QuizCreateRequest(BaseModel):
        question: str = Field(min_length=1)
        correct: str = Field(min_length=1)
        wrong: list[str] = Field(min_length=1)

    class QuizAnswerRequest(BaseModel):
        answer: str = Field(min_length=1)

    class HealthGoalRequest(BaseModel):
        daily_calories: int = Field(ge=0, default=0)
        daily_protein_g: float = Field(ge=0, default=0.0)
        daily_carbs_g: float = Field(ge=0, default=0.0)
        daily_fat_g: float = Field(ge=0, default=0.0)

    class UserPreferencesRequest(BaseModel):
        preferred_categories: list[str] | None = None
        excluded_allergens: list[str] | None = None
        max_cooking_time: int = 0

    class IngredientNutritionRequest(BaseModel):
        name: str = Field(min_length=1)
        calories: float = Field(ge=0, default=0)
        protein: float = Field(ge=0, default=0)
        carbs: float = Field(ge=0, default=0)
        fat: float = Field(ge=0, default=0)

    class CuratedListRequest(BaseModel):
        title: str = Field(min_length=1, max_length=200)
        description: str = ""

    class CuratedListAddRequest(BaseModel):
        recipe_id: int
        sort_order: int = 0

    class RatingReviewRequest(BaseModel):
        text: str = Field(min_length=1, max_length=2000)

    class IngredientGroupInput(BaseModel):
        group_name: str = Field(min_length=1)
        sort_order: int = 0

    class IngredientGroupsRequest(BaseModel):
        groups: list[IngredientGroupInput] = Field(min_length=1)

    class DraftRequest(BaseModel):
        title: str = Field(min_length=1)
        data_json: str = Field(min_length=1)

    class CookingProgressRequest(BaseModel):
        current_step: int = Field(ge=0)
        total_steps: int = Field(ge=1)

    class RecipeSourceRequest(BaseModel):
        url: str = Field(min_length=1)
        source_name: str = ""

    class CostLogRequest2(BaseModel):
        amount: float = Field(gt=0)
        note: str = ""

    class ReactionRequest(BaseModel):
        emoji: str = Field(min_length=1, max_length=10)

    class PlaylistRequest(BaseModel):
        name: str = Field(min_length=1, max_length=100)

    class PlaylistAddRequest(BaseModel):
        recipe_id: int
        sort_order: int = 0

    class SkillLevelRequest(BaseModel):
        skill_level: str = Field(pattern="^(beginner|intermediate|advanced|expert)$")

    class ServingsRequest(BaseModel):
        servings: int = Field(ge=1)

    class HashtagRequest(BaseModel):
        hashtag: str = Field(min_length=1)

    class PriceAlertRequest(BaseModel):
        ingredient: str = Field(min_length=1)
        max_price: float = Field(gt=0)

    class CollaboratorRequest(BaseModel):
        user_id: int
        role: str = "editor"

    class CookingClassRequest(BaseModel):
        title: str = Field(min_length=1)
        description: str = ""
        scheduled_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
        max_participants: int = Field(ge=1, default=20)

    class BundleRequest(BaseModel):
        name: str = Field(min_length=1)
        description: str = ""

    class BundleAddRequest(BaseModel):
        recipe_id: int
        sort_order: int = 0

    class MealPrepRequest2(BaseModel):
        name: str = Field(min_length=1)
        prep_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
        servings: int = Field(ge=1, default=4)

    class FlavorProfileRequest(BaseModel):
        sweet: int = Field(ge=0, le=5, default=0)
        salty: int = Field(ge=0, le=5, default=0)
        sour: int = Field(ge=0, le=5, default=0)
        bitter: int = Field(ge=0, le=5, default=0)
        umami: int = Field(ge=0, le=5, default=0)
        spicy: int = Field(ge=0, le=5, default=0)

    class JournalRequest(BaseModel):
        date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
        content: str = Field(min_length=1)
        recipe_id: int | None = None
        mood: str = ""

    class PairingRequest(BaseModel):
        ingredient_a: str = Field(min_length=1)
        ingredient_b: str = Field(min_length=1)
        score: int = Field(ge=1, le=10, default=5)

    class MoodTagsRequest(BaseModel):
        moods: list[str] = Field(min_length=1)

    class SpeedChallengeRequest(BaseModel):
        target_minutes: int = Field(gt=0)

    class SpeedResultRequest(BaseModel):
        actual_minutes: int = Field(gt=0)

    class GiftRequest(BaseModel):
        recipient_id: int
        recipe_id: int
        message: str = ""

    class IngredientInfoRequest(BaseModel):
        name: str = Field(min_length=1)
        description: str = ""
        tips: str = ""
        storage: str = ""

    class TechniqueRequest(BaseModel):
        name: str = Field(min_length=1)
        description: str = ""
        difficulty: str = "easy"

    class EndorsementRequest(BaseModel):
        comment: str = ""

    class OriginRequest(BaseModel):
        name: str = Field(min_length=1)
        origin: str = Field(min_length=1)
        description: str = ""

    class EventRequest(BaseModel):
        name: str = Field(min_length=1)
        event_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
        description: str = ""

    class GroupCookRequest(BaseModel):
        recipe_id: int
        cook_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
        max_participants: int = Field(ge=2, default=8)

    class StoreRequest(BaseModel):
        name: str = Field(min_length=1)
        location: str = ""
        description: str = ""

    class StoreIngredientRequest(BaseModel):
        ingredient: str = Field(min_length=1)
        price: float = Field(ge=0, default=0)

    class StoryRequest(BaseModel):
        story: str = Field(min_length=1)

    class FaqRequest(BaseModel):
        question: str = Field(min_length=1)
        answer: str = Field(min_length=1)
        category: str = "general"

    class AchievementRequest(BaseModel):
        code: str = Field(min_length=1)
        name: str = Field(min_length=1)
        description: str = ""
        condition_type: str = Field(min_length=1)
        condition_value: int = Field(ge=0)

    class TemplateRequest(BaseModel):
        name: str = Field(min_length=1)
        description: str = ""
        default_data_json: str = Field(min_length=1)

    class TimerPresetRequest(BaseModel):
        name: str = Field(min_length=1)
        timers_json: str = Field(min_length=1)

    class ApprovalRejectRequest(BaseModel):
        reason: str = ""

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

    @app.get("/api/recipes/category/{category}", tags=["category"])
    def api_recipes_by_category(category: str, limit: int = Query(50, ge=1, le=100)):
        """카테고리별 레시피"""
        cur = db.conn.execute(
            "SELECT r.*, u.username AS author_name FROM recipes r JOIN users u ON r.author_id=u.id WHERE r.category=? ORDER BY r.created_at DESC LIMIT ?",
            (category, limit),
        )
        from recipe_service.models import Recipe
        recipes = [Recipe(**dict(row)) for row in cur.fetchall()]
        return {"category": category, "recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.post("/api/recipes/publish-scheduled", tags=["schedule"])
    def api_publish_scheduled():
        """예약된 레시피 공개"""
        count = db.publish_scheduled_recipes()
        return {"success": True, "published_count": count}

    @app.get("/api/recipes/personalized", tags=["preferences"])
    def api_personalized_recipes(limit: int = Query(20, ge=1, le=100), authorization: str | None = Header(None)):
        """개인화 레시피 추천"""
        user = _get_user(authorization)
        recipes = db.get_personalized_recipes(user.id, limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.get("/api/recipes/autocomplete", tags=["search"])
    def api_autocomplete(prefix: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
        """재료 자동완성"""
        return {"suggestions": db.autocomplete_ingredient(prefix, limit=limit)}

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
    # RECIPE CATEGORY (Feature 41)
    # =====================

    @app.put("/api/recipes/{recipe_id}/category", tags=["category"])
    def api_set_category(recipe_id: int, req: CategoryRequest, authorization: str | None = Header(None)):
        """레시피 카테고리 설정"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        db.set_recipe_category(recipe_id, req.category)
        return {"success": True, "category": req.category}

    # =====================
    # EQUIPMENT (Feature 42)
    # =====================

    @app.put("/api/recipes/{recipe_id}/equipment", tags=["equipment"])
    def api_set_equipment(recipe_id: int, req: EquipmentRequest, authorization: str | None = Header(None)):
        """레시피 필요 장비 설정"""
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        equipment = db.set_equipment(recipe_id, req.equipment)
        return {"success": True, "equipment": equipment}

    @app.get("/api/recipes/{recipe_id}/equipment", tags=["equipment"])
    def api_get_equipment(recipe_id: int):
        """레시피 필요 장비 조회"""
        return {"equipment": db.get_equipment(recipe_id)}

    # =====================
    # AUTO DIFFICULTY (Feature 43)
    # =====================

    @app.get("/api/recipes/{recipe_id}/auto-difficulty", tags=["difficulty"])
    def api_auto_difficulty(recipe_id: int):
        """레시피 자동 난이도 계산"""
        try:
            difficulty = db.calculate_difficulty(recipe_id)
            return {"recipe_id": recipe_id, "calculated_difficulty": difficulty}
        except ValueError as e:
            raise HTTPException(404, str(e))

    # =====================
    # BOOKMARK SORTING (Feature 44)
    # =====================

    @app.get("/api/users/{user_id}/bookmarks/sorted", tags=["bookmarks"])
    def api_sorted_bookmarks(user_id: int, sort: str = Query("recent", pattern="^(recent|title|rating)$")):
        """정렬된 북마크 목록"""
        recipes = db.get_user_bookmarks_sorted(user_id, sort_by=sort)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    # =====================
    # CLONE RECIPE (Feature 45)
    # =====================

    @app.post("/api/recipes/{recipe_id}/clone", tags=["clone"])
    def api_clone_recipe(recipe_id: int, authorization: str | None = Header(None)):
        """레시피 복제 (내 레시피로)"""
        user = _get_user(authorization)
        try:
            cloned = db.clone_recipe(recipe_id, user.id)
            return {"success": True, "recipe": _recipe_dict(cloned)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    # =====================
    # USER NOTES (Feature 46)
    # =====================

    @app.put("/api/recipes/{recipe_id}/note", tags=["notes"])
    def api_set_note(recipe_id: int, req: UserNoteRequest, authorization: str | None = Header(None)):
        """레시피에 개인 메모 작성"""
        user = _get_user(authorization)
        note = db.set_user_note(user.id, recipe_id, req.content)
        return {"success": True, "note": {"content": note.content, "updated_at": note.updated_at}}

    @app.get("/api/recipes/{recipe_id}/note", tags=["notes"])
    def api_get_note(recipe_id: int, authorization: str | None = Header(None)):
        """레시피 개인 메모 조회"""
        user = _get_user(authorization)
        note = db.get_user_note(user.id, recipe_id)
        if not note:
            return {"note": None}
        return {"note": {"content": note.content, "updated_at": note.updated_at}}

    # =====================
    # UNIT CONVERSION (Feature 47)
    # =====================

    @app.get("/api/convert-unit", tags=["unit"])
    def api_convert_unit(
        value: float = Query(..., gt=0),
        from_unit: str = Query(...),
        to_unit: str = Query(...),
    ):
        """단위 변환"""
        from recipe_service.models import Database as DB
        result = DB.convert_unit(value, from_unit, to_unit)
        if result is None:
            raise HTTPException(400, f"변환 불가: {from_unit} → {to_unit}")
        return {"value": value, "from_unit": from_unit, "to_unit": to_unit, "result": result}

    # =====================
    # SERVING SCALER (Feature 48)
    # =====================

    @app.get("/api/recipes/{recipe_id}/scale", tags=["scale"])
    def api_scale_recipe(recipe_id: int, servings: int = Query(..., ge=1)):
        """레시피 인분 스케일링"""
        try:
            return db.scale_recipe(recipe_id, servings)
        except ValueError as e:
            raise HTTPException(404, str(e))

    # =====================
    # RECIPE VISIBILITY (Feature 49)
    # =====================

    @app.put("/api/recipes/{recipe_id}/visibility", tags=["visibility"])
    def api_set_visibility(recipe_id: int, req: VisibilityRequest, authorization: str | None = Header(None)):
        """레시피 공개/비공개 설정"""
        user = _get_user(authorization)
        if not db.set_recipe_visibility(recipe_id, user.id, req.is_public):
            raise HTTPException(403, "권한이 없습니다")
        return {"success": True, "is_public": req.is_public}

    # =====================
    # SEARCH HISTORY (Feature 50)
    # =====================

    @app.get("/api/search-history", tags=["search"])
    def api_get_search_history(limit: int = Query(20, ge=1, le=100), authorization: str | None = Header(None)):
        """검색 기록 조회"""
        user = _get_user(authorization)
        return {"history": db.get_search_history(user.id, limit=limit)}

    @app.delete("/api/search-history", tags=["search"])
    def api_clear_search_history(authorization: str | None = Header(None)):
        """검색 기록 삭제"""
        user = _get_user(authorization)
        count = db.clear_search_history(user.id)
        return {"success": True, "cleared_count": count}

    @app.post("/api/search-history", tags=["search"])
    def api_record_search(req: SearchRequest, authorization: str | None = Header(None)):
        """검색 기록 저장"""
        user = _get_user(authorization)
        db.record_search(user.id, req.query)
        return {"success": True}

    # =====================
    # INGREDIENT AUTOCOMPLETE (Feature 51)
    # =====================

    @app.get("/api/ingredients/autocomplete", tags=["ingredients"])
    def api_ingredient_autocomplete(prefix: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
        """재료 자동완성"""
        return {"suggestions": db.autocomplete_ingredient(prefix, limit=limit)}

    # =====================
    # SCHEDULED PUBLISHING (Feature 52)
    # =====================

    @app.post("/api/recipes/{recipe_id}/schedule", tags=["schedule"])
    def api_schedule_recipe(recipe_id: int, req: ScheduleRequest, authorization: str | None = Header(None)):
        """레시피 예약 공개"""
        user = _get_user(authorization)
        if not db.schedule_recipe(recipe_id, user.id, req.publish_at):
            raise HTTPException(403, "권한이 없습니다")
        return {"success": True, "publish_at": req.publish_at}

    # =====================
    # ACTIVITY LOG (Feature 53)
    # =====================

    @app.get("/api/activity-log", tags=["activity"])
    def api_activity_log(limit: int = Query(50, ge=1, le=100), authorization: str | None = Header(None)):
        """내 활동 로그"""
        user = _get_user(authorization)
        logs = db.get_activity_log(user.id, limit=limit)
        return {"logs": [{"action": l.action, "detail": l.detail, "created_at": l.created_at} for l in logs]}

    @app.post("/api/activity-log", tags=["activity"])
    def api_log_activity(authorization: str | None = Header(None)):
        """활동 기록 (내부용)"""
        user = _get_user(authorization)
        db.log_activity(user.id, "api_call")
        return {"success": True}

    # =====================
    # FRESHNESS SCORE (Feature 54)
    # =====================

    @app.get("/api/recipes/{recipe_id}/freshness", tags=["freshness"])
    def api_freshness_score(recipe_id: int):
        """레시피 신선도 점수"""
        return db.get_freshness_score(recipe_id)

    # =====================
    # FOLLOWERS-ONLY RECIPES (Feature 55)
    # =====================

    @app.get("/api/users/{user_id}/followers-recipes", tags=["follow"])
    def api_followers_only(user_id: int, authorization: str | None = Header(None)):
        """팔로워 전용 레시피"""
        viewer = _get_user(authorization)
        recipes = db.get_followers_only_recipes(viewer.id, user_id)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    # =====================
    # CURATED LISTS (Feature 56)
    # =====================

    @app.post("/api/curated-lists", tags=["curated"])
    def api_create_curated(req: CuratedListRequest, authorization: str | None = Header(None)):
        """큐레이션 리스트 생성"""
        user = _get_user(authorization)
        cl = db.create_curated_list(user.id, req.title, req.description)
        return {"success": True, "list": {"id": cl.id, "title": cl.title}}

    @app.post("/api/curated-lists/{list_id}/recipes", tags=["curated"])
    def api_add_to_curated(list_id: int, req: CuratedListAddRequest, authorization: str | None = Header(None)):
        """큐레이션 리스트에 레시피 추가"""
        _get_user(authorization)
        db.add_to_curated_list(list_id, req.recipe_id, req.sort_order)
        return {"success": True}

    @app.get("/api/curated-lists/{list_id}/recipes", tags=["curated"])
    def api_curated_recipes(list_id: int):
        """큐레이션 리스트 레시피"""
        recipes = db.get_curated_list_recipes(list_id)
        return {"recipes": [_recipe_dict(r) for r in recipes], "count": len(recipes)}

    @app.get("/api/curated-lists", tags=["curated"])
    def api_all_curated():
        """전체 큐레이션 리스트"""
        lists = db.get_all_curated_lists()
        return {"lists": [{"id": c.id, "title": c.title, "description": c.description} for c in lists]}

    # =====================
    # LIKE TIMELINE (Feature 57)
    # =====================

    @app.get("/api/like-timeline", tags=["likes"])
    def api_like_timeline(limit: int = Query(50, ge=1, le=100), authorization: str | None = Header(None)):
        """내 좋아요 타임라인"""
        user = _get_user(authorization)
        return {"timeline": db.get_like_timeline(user.id, limit=limit)}

    # =====================
    # INGREDIENT NUTRITION (Feature 58)
    # =====================

    @app.put("/api/ingredient-nutrition", tags=["nutrition"])
    def api_set_ingredient_nutrition(req: IngredientNutritionRequest):
        """재료 영양 정보 설정"""
        info = db.set_ingredient_nutrition(req.name, req.calories, req.protein, req.carbs, req.fat)
        return {"success": True, "nutrition": {"name": info.name, "calories_per_100g": info.calories_per_100g}}

    @app.get("/api/ingredient-nutrition/{name}", tags=["nutrition"])
    def api_get_ingredient_nutrition(name: str):
        """재료 영양 정보 조회"""
        info = db.get_ingredient_nutrition(name)
        if not info:
            return {"nutrition": None}
        return {"nutrition": {"name": info.name, "calories_per_100g": info.calories_per_100g,
                              "protein_per_100g": info.protein_per_100g, "carbs_per_100g": info.carbs_per_100g,
                              "fat_per_100g": info.fat_per_100g}}

    # =====================
    # TRENDING TAGS (Feature 59)
    # =====================

    @app.get("/api/tags/trending", tags=["tags"])
    def api_trending_tags(days: int = Query(7, ge=1, le=90), limit: int = Query(10, ge=1, le=50)):
        """트렌딩 태그"""
        return {"tags": db.get_trending_tags(days=days, limit=limit)}

    # =====================
    # USER PREFERENCES (Feature 60)
    # =====================

    @app.put("/api/preferences", tags=["preferences"])
    def api_set_preferences(req: UserPreferencesRequest, authorization: str | None = Header(None)):
        """사용자 선호도 설정"""
        user = _get_user(authorization)
        db.set_user_preferences(user.id, req.preferred_categories, req.excluded_allergens, req.max_cooking_time)
        return {"success": True}

    @app.get("/api/preferences", tags=["preferences"])
    def api_get_preferences(authorization: str | None = Header(None)):
        """사용자 선호도 조회"""
        user = _get_user(authorization)
        pref = db.get_user_preferences(user.id)
        if not pref:
            return {"preferences": None}
        return {"preferences": {
            "preferred_categories": pref.preferred_categories,
            "excluded_allergens": pref.excluded_allergens,
            "max_cooking_time": pref.max_cooking_time,
        }}

    # =====================
    # RECIPE TRANSLATION (Feature 61)
    # =====================

    @app.put("/api/recipes/{recipe_id}/translations", tags=["translation"])
    def api_set_translation(recipe_id: int, req: TranslationRequest, authorization: str | None = Header(None)):
        """레시피 번역 추가"""
        _get_user(authorization)
        t = db.set_translation(recipe_id, req.language, req.title, req.description)
        return {"success": True, "translation": {"language": t.language, "title": t.title}}

    @app.get("/api/recipes/{recipe_id}/translations", tags=["translation"])
    def api_get_translations(recipe_id: int):
        """레시피 번역 목록"""
        translations = db.get_translations(recipe_id)
        return {"translations": [{"language": t.language, "title": t.title, "description": t.description} for t in translations]}

    # =====================
    # PANTRY (Feature 62)
    # =====================

    @app.post("/api/pantry", tags=["pantry"])
    def api_add_pantry(req: PantryItemRequest, authorization: str | None = Header(None)):
        """식료품 저장실에 항목 추가"""
        user = _get_user(authorization)
        item = db.add_pantry_item(user.id, req.name, req.amount, req.unit, req.expiry_date)
        return {"success": True, "item": {"id": item.id, "name": item.name}}

    @app.get("/api/pantry", tags=["pantry"])
    def api_get_pantry(authorization: str | None = Header(None)):
        """내 식료품 저장실"""
        user = _get_user(authorization)
        items = db.get_pantry(user.id)
        return {"items": [{"id": i.id, "name": i.name, "amount": i.amount, "unit": i.unit, "expiry_date": i.expiry_date} for i in items]}

    @app.delete("/api/pantry/{item_id}", tags=["pantry"])
    def api_delete_pantry(item_id: int, authorization: str | None = Header(None)):
        """식료품 항목 삭제"""
        user = _get_user(authorization)
        if not db.delete_pantry_item(item_id, user.id):
            raise HTTPException(404, "항목을 찾을 수 없습니다")
        return {"success": True}

    @app.get("/api/pantry/recipes", tags=["pantry"])
    def api_pantry_recipes(min_match: float = Query(0.5, ge=0, le=1), authorization: str | None = Header(None)):
        """식료품 기반 레시피 추천"""
        user = _get_user(authorization)
        return {"recipes": db.find_recipes_from_pantry(user.id, min_match=min_match)}

    # =====================
    # SHARE STATS (Feature 63)
    # =====================

    @app.get("/api/recipes/{recipe_id}/share-stats", tags=["share"])
    def api_share_stats(recipe_id: int):
        """레시피 공유 통계"""
        return db.get_share_stats(recipe_id)

    # =====================
    # RECOMMENDATIONS WITH REASONS (Feature 64)
    # =====================

    @app.get("/api/recipes/{recipe_id}/recommendations", tags=["recommendations"])
    def api_recommendations(recipe_id: int, limit: int = Query(10, ge=1, le=50)):
        """이유 포함 추천"""
        return {"recommendations": db.get_recommendations_with_reasons(recipe_id, limit=limit)}

    # =====================
    # NOTIFICATION PREFERENCES (Feature 65)
    # =====================

    @app.put("/api/notification-prefs", tags=["notifications"])
    def api_set_notif_prefs(req: NotificationPrefRequest, authorization: str | None = Header(None)):
        """알림 설정"""
        user = _get_user(authorization)
        db.set_notification_prefs(user.id, req.likes, req.comments, req.follows, req.challenges)
        return {"success": True}

    @app.get("/api/notification-prefs", tags=["notifications"])
    def api_get_notif_prefs(authorization: str | None = Header(None)):
        """알림 설정 조회"""
        user = _get_user(authorization)
        pref = db.get_notification_prefs(user.id)
        return {"prefs": {"likes": pref.likes, "comments": pref.comments, "follows": pref.follows, "challenges": pref.challenges}}

    # =====================
    # ATTEMPT LOGS (Feature 66)
    # =====================

    @app.post("/api/recipes/{recipe_id}/attempts", tags=["attempts"])
    def api_log_attempt(recipe_id: int, req: AttemptLogRequest, authorization: str | None = Header(None)):
        """레시피 시도 기록"""
        user = _get_user(authorization)
        log = db.log_attempt(user.id, recipe_id, req.status, req.note)
        return {"success": True, "attempt": {"id": log.id, "status": log.status}}

    @app.get("/api/attempts", tags=["attempts"])
    def api_get_attempts(recipe_id: int | None = Query(None), limit: int = Query(50, ge=1, le=100), authorization: str | None = Header(None)):
        """내 시도 기록"""
        user = _get_user(authorization)
        logs = db.get_attempt_logs(user.id, recipe_id=recipe_id, limit=limit)
        return {"attempts": [{"id": l.id, "recipe_id": l.recipe_id, "status": l.status, "note": l.note, "created_at": l.created_at} for l in logs]}

    # =====================
    # POPULAR SEARCHES (Feature 67)
    # =====================

    @app.get("/api/search/popular", tags=["search"])
    def api_popular_searches(limit: int = Query(20, ge=1, le=100)):
        """인기 검색어"""
        return {"searches": db.get_popular_searches(limit=limit)}

    # =====================
    # RECIPE QUIZ (Feature 68)
    # =====================

    @app.post("/api/recipes/{recipe_id}/quizzes", tags=["quiz"])
    def api_create_quiz(recipe_id: int, req: QuizCreateRequest, authorization: str | None = Header(None)):
        """레시피 퀴즈 생성"""
        _get_user(authorization)
        try:
            quiz = db.create_quiz(recipe_id, req.question, req.correct, req.wrong)
            return {"success": True, "quiz": {"id": quiz.id, "question": quiz.question}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/quizzes", tags=["quiz"])
    def api_get_quizzes(recipe_id: int):
        """레시피 퀴즈 목록"""
        return {"quizzes": db.get_recipe_quizzes(recipe_id)}

    @app.post("/api/quizzes/{quiz_id}/answer", tags=["quiz"])
    def api_answer_quiz(quiz_id: int, req: QuizAnswerRequest):
        """퀴즈 답변 확인"""
        try:
            return db.check_quiz_answer(quiz_id, req.answer)
        except ValueError as e:
            raise HTTPException(404, str(e))

    # =====================
    # HEALTH GOALS (Feature 69-70)
    # =====================

    @app.put("/api/health-goal", tags=["health"])
    def api_set_health_goal(req: HealthGoalRequest, authorization: str | None = Header(None)):
        """건강 목표 설정"""
        user = _get_user(authorization)
        db.set_health_goal(user.id, req.daily_calories, req.daily_protein_g, req.daily_carbs_g, req.daily_fat_g)
        return {"success": True}

    @app.get("/api/health-goal", tags=["health"])
    def api_get_health_goal(authorization: str | None = Header(None)):
        """건강 목표 조회"""
        user = _get_user(authorization)
        goal = db.get_health_goal(user.id)
        if not goal:
            return {"goal": None}
        return {"goal": {"daily_calories": goal.daily_calories, "daily_protein_g": goal.daily_protein_g,
                         "daily_carbs_g": goal.daily_carbs_g, "daily_fat_g": goal.daily_fat_g}}

    @app.get("/api/meal-plans/nutrition", tags=["health"])
    def api_meal_plan_nutrition(date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"), authorization: str | None = Header(None)):
        """식단 영양 분석"""
        user = _get_user(authorization)
        return db.check_meal_plan_nutrition(user.id, date)

    # =====================
    # RATING REVIEWS (Feature 71)
    # =====================

    @app.post("/api/recipes/{recipe_id}/rating-reviews", tags=["ratings"])
    def api_add_rating_review(recipe_id: int, req: RatingReviewRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        review = db.add_rating_review(0, user.id, recipe_id, req.text)
        return {"success": True, "review": {"id": review.id, "text": review.text}}

    @app.get("/api/recipes/{recipe_id}/rating-reviews", tags=["ratings"])
    def api_get_rating_reviews(recipe_id: int, limit: int = Query(50, ge=1, le=100)):
        reviews = db.get_rating_reviews(recipe_id, limit=limit)
        return {"reviews": [{"id": r.id, "user_id": r.user_id, "text": r.text, "created_at": r.created_at} for r in reviews]}

    # =====================
    # INGREDIENT GROUPS (Feature 72)
    # =====================

    @app.put("/api/recipes/{recipe_id}/ingredient-groups", tags=["ingredients"])
    def api_set_ingredient_groups(recipe_id: int, req: IngredientGroupsRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        recipe = db.get_recipe(recipe_id)
        if not recipe or recipe.author_id != user.id:
            raise HTTPException(403, "권한이 없습니다")
        groups = db.set_ingredient_groups(recipe_id, [g.model_dump() for g in req.groups])
        return {"success": True, "groups": groups}

    @app.get("/api/recipes/{recipe_id}/ingredient-groups", tags=["ingredients"])
    def api_get_ingredient_groups(recipe_id: int):
        return {"groups": db.get_ingredient_groups(recipe_id)}

    # =====================
    # RECIPE DRAFTS (Feature 73)
    # =====================

    @app.post("/api/drafts", tags=["drafts"])
    def api_save_draft(req: DraftRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        draft = db.save_draft(user.id, req.title, req.data_json)
        return {"success": True, "draft": {"id": draft.id, "title": draft.title}}

    @app.get("/api/drafts", tags=["drafts"])
    def api_get_drafts(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        drafts = db.get_drafts(user.id)
        return {"drafts": [{"id": d.id, "title": d.title, "updated_at": d.updated_at} for d in drafts]}

    @app.delete("/api/drafts/{draft_id}", tags=["drafts"])
    def api_delete_draft(draft_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        if not db.delete_draft(draft_id, user.id):
            raise HTTPException(404, "임시저장을 찾을 수 없습니다")
        return {"success": True}

    # =====================
    # COOKING PROGRESS (Feature 74)
    # =====================

    @app.put("/api/recipes/{recipe_id}/cooking-progress", tags=["cooking"])
    def api_update_progress(recipe_id: int, req: CookingProgressRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        p = db.update_cooking_progress(user.id, recipe_id, req.current_step, req.total_steps)
        return {"success": True, "progress": {"current_step": p.current_step, "total_steps": p.total_steps}}

    @app.get("/api/recipes/{recipe_id}/cooking-progress", tags=["cooking"])
    def api_get_progress(recipe_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        p = db.get_cooking_progress(user.id, recipe_id)
        if not p:
            return {"progress": None}
        return {"progress": {"current_step": p.current_step, "total_steps": p.total_steps}}

    @app.delete("/api/recipes/{recipe_id}/cooking-progress", tags=["cooking"])
    def api_clear_progress(recipe_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        db.clear_cooking_progress(user.id, recipe_id)
        return {"success": True}

    # =====================
    # RECIPE SOURCE (Feature 75)
    # =====================

    @app.put("/api/recipes/{recipe_id}/source", tags=["source"])
    def api_set_source(recipe_id: int, req: RecipeSourceRequest, authorization: str | None = Header(None)):
        _get_user(authorization)
        src = db.set_recipe_source(recipe_id, req.url, req.source_name)
        return {"success": True, "source": {"url": src.url, "source_name": src.source_name}}

    @app.get("/api/recipes/{recipe_id}/source", tags=["source"])
    def api_get_source(recipe_id: int):
        src = db.get_recipe_source(recipe_id)
        if not src:
            return {"source": None}
        return {"source": {"url": src.url, "source_name": src.source_name}}

    # =====================
    # MENU SUGGESTION (Feature 76)
    # =====================

    @app.get("/api/menu-suggestions", tags=["menu"])
    def api_menu_suggestions(meal_type: str = Query("lunch"), limit: int = Query(5, ge=1, le=20)):
        recipes = db.get_menu_suggestions(meal_type, limit=limit)
        return {"meal_type": meal_type, "suggestions": [_recipe_dict(r) for r in recipes]}

    # =====================
    # COST LOG (Feature 77)
    # =====================

    @app.post("/api/recipes/{recipe_id}/cost-log", tags=["cost"])
    def api_log_cost(recipe_id: int, req: CostLogRequest2, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        log = db.log_cooking_cost(user.id, recipe_id, req.amount, req.note)
        return {"success": True, "cost_log": {"id": log.id, "amount": log.amount}}

    @app.get("/api/cost-logs", tags=["cost"])
    def api_get_cost_logs(limit: int = Query(50, ge=1, le=100), authorization: str | None = Header(None)):
        user = _get_user(authorization)
        logs = db.get_cost_logs(user.id, limit=limit)
        return {"logs": [{"id": l.id, "recipe_id": l.recipe_id, "amount": l.amount, "note": l.note, "created_at": l.created_at} for l in logs]}

    @app.get("/api/cost-total", tags=["cost"])
    def api_total_cost(days: int = Query(30, ge=1), authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"total": db.get_total_cost(user.id, days=days), "days": days}

    # =====================
    # REACTIONS (Feature 78)
    # =====================

    @app.post("/api/recipes/{recipe_id}/reactions", tags=["reactions"])
    def api_add_reaction(recipe_id: int, req: ReactionRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        try:
            r = db.add_reaction(user.id, recipe_id, req.emoji)
            return {"success": True, "emoji": r.emoji}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.delete("/api/recipes/{recipe_id}/reactions/{emoji}", tags=["reactions"])
    def api_remove_reaction(recipe_id: int, emoji: str, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        db.remove_reaction(user.id, recipe_id, emoji)
        return {"success": True}

    @app.get("/api/recipes/{recipe_id}/reactions", tags=["reactions"])
    def api_get_reactions(recipe_id: int):
        return {"reactions": db.get_reactions(recipe_id)}

    # =====================
    # COOKING PLAYLIST (Feature 79)
    # =====================

    @app.post("/api/playlists", tags=["playlist"])
    def api_create_playlist(req: PlaylistRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        pl = db.create_playlist(user.id, req.name)
        return {"success": True, "playlist": {"id": pl.id, "name": pl.name}}

    @app.post("/api/playlists/{playlist_id}/recipes", tags=["playlist"])
    def api_add_to_playlist(playlist_id: int, req: PlaylistAddRequest, authorization: str | None = Header(None)):
        _get_user(authorization)
        db.add_to_playlist(playlist_id, req.recipe_id, req.sort_order)
        return {"success": True}

    @app.get("/api/playlists/{playlist_id}/recipes", tags=["playlist"])
    def api_playlist_recipes(playlist_id: int):
        recipes = db.get_playlist_recipes(playlist_id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    @app.get("/api/playlists", tags=["playlist"])
    def api_user_playlists(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        pls = db.get_user_playlists(user.id)
        return {"playlists": [{"id": p.id, "name": p.name, "created_at": p.created_at} for p in pls]}

    @app.delete("/api/playlists/{playlist_id}", tags=["playlist"])
    def api_delete_playlist(playlist_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        if not db.delete_playlist(playlist_id, user.id):
            raise HTTPException(404, "플레이리스트를 찾을 수 없습니다")
        return {"success": True}

    # =====================
    # CERTIFICATION (Feature 80)
    # =====================

    @app.post("/api/recipes/{recipe_id}/certify", tags=["certification"])
    def api_certify(recipe_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        db.certify_recipe(recipe_id, user.id)
        return {"success": True}

    @app.get("/api/recipes/{recipe_id}/certified", tags=["certification"])
    def api_is_certified(recipe_id: int):
        return {"certified": db.is_certified(recipe_id)}

    @app.get("/api/certified-recipes", tags=["certification"])
    def api_certified_recipes(limit: int = Query(50, ge=1, le=100)):
        recipes = db.get_certified_recipes(limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # INGREDIENT SEASONS (Feature 81)
    # =====================

    @app.put("/api/ingredient-seasons/{name}", tags=["seasons"])
    def api_set_ingredient_season(name: str, req: SeasonRequest):
        db.set_ingredient_season(name, [req.season])
        return {"success": True}

    @app.get("/api/ingredient-seasons/{season}", tags=["seasons"])
    def api_seasonal_ingredients(season: str):
        return {"ingredients": db.get_seasonal_ingredients(season)}

    # =====================
    # TIMER PRESETS (Feature 82)
    # =====================

    @app.post("/api/timer-presets", tags=["timers"])
    def api_save_timer_preset(req: TimerPresetRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        preset = db.save_timer_preset(user.id, req.name, req.timers_json)
        return {"success": True, "preset": {"id": preset.id, "name": preset.name}}

    @app.get("/api/timer-presets", tags=["timers"])
    def api_get_timer_presets(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        presets = db.get_timer_presets(user.id)
        return {"presets": [{"id": p.id, "name": p.name, "timers_json": p.timers_json} for p in presets]}

    @app.delete("/api/timer-presets/{preset_id}", tags=["timers"])
    def api_delete_timer_preset(preset_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        if not db.delete_timer_preset(preset_id, user.id):
            raise HTTPException(404, "프리셋을 찾을 수 없습니다")
        return {"success": True}

    # =====================
    # EDIT HISTORY (Feature 83)
    # =====================

    @app.get("/api/recipes/{recipe_id}/edit-history", tags=["history"])
    def api_edit_history(recipe_id: int, limit: int = Query(50, ge=1, le=100)):
        logs = db.get_edit_history(recipe_id, limit=limit)
        return {"history": [{"field": l.field_name, "old": l.old_value, "new": l.new_value, "edited_at": l.edited_at} for l in logs]}

    # =====================
    # SOCIAL SHARES (Feature 84)
    # =====================

    @app.post("/api/recipes/{recipe_id}/social-share", tags=["share"])
    def api_track_social_share(recipe_id: int, platform: str = Query(...)):
        db.track_social_share(recipe_id, platform)
        return {"success": True}

    @app.get("/api/recipes/{recipe_id}/social-shares", tags=["share"])
    def api_get_social_shares(recipe_id: int):
        return {"shares": db.get_social_shares(recipe_id)}

    # =====================
    # TEMPLATES (Feature 85)
    # =====================

    @app.post("/api/templates", tags=["templates"])
    def api_create_template(req: TemplateRequest):
        try:
            t = db.create_template(req.name, req.description, req.default_data_json)
            return {"success": True, "template": {"id": t.id, "name": t.name}}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/templates", tags=["templates"])
    def api_get_templates():
        templates = db.get_templates()
        return {"templates": [{"id": t.id, "name": t.name, "description": t.description} for t in templates]}

    # =====================
    # COOKING SKILL (Feature 86)
    # =====================

    @app.put("/api/cooking-skill", tags=["skill"])
    def api_set_skill(req: SkillLevelRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return db.set_cooking_skill(user.id, req.skill_level)

    @app.get("/api/cooking-skill", tags=["skill"])
    def api_get_skill(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"skill_level": db.get_cooking_skill(user.id)}

    # =====================
    # DEFAULT SERVINGS (Feature 87)
    # =====================

    @app.put("/api/default-servings", tags=["servings"])
    def api_set_servings(req: ServingsRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return db.set_default_servings(user.id, req.servings)

    @app.get("/api/default-servings", tags=["servings"])
    def api_get_servings(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"default_servings": db.get_default_servings(user.id)}

    # =====================
    # RECIPE ARCHIVE (Feature 88)
    # =====================

    @app.post("/api/recipes/{recipe_id}/archive", tags=["archive"])
    def api_archive(recipe_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        db.archive_recipe(recipe_id, user.id)
        return {"success": True}

    @app.delete("/api/recipes/{recipe_id}/archive", tags=["archive"])
    def api_unarchive(recipe_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        db.unarchive_recipe(recipe_id, user.id)
        return {"success": True}

    @app.get("/api/archived-recipes", tags=["archive"])
    def api_archived(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        recipes = db.get_archived_recipes(user.id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # INGREDIENT STATS (Feature 89)
    # =====================

    @app.get("/api/ingredient-stats", tags=["stats"])
    def api_ingredient_stats(limit: int = Query(20, ge=1, le=100)):
        return {"stats": db.get_ingredient_usage_stats(limit=limit)}

    @app.get("/api/users/{user_id}/ingredient-stats", tags=["stats"])
    def api_user_ingredient_stats(user_id: int, limit: int = Query(20, ge=1, le=100)):
        return {"stats": db.get_user_ingredient_stats(user_id, limit=limit)}

    # =====================
    # AUTO MENU (Feature 90)
    # =====================

    @app.post("/api/auto-menu", tags=["meal_plan"])
    def api_auto_menu(start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"), authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"menu": db.generate_weekly_menu(user.id, start_date)}

    # =====================
    # COST COMPARE (Feature 91)
    # =====================

    @app.get("/api/cost-compare", tags=["cost"])
    def api_cost_compare(ids: str = Query(...)):
        recipe_ids = [int(x) for x in ids.split(",") if x.strip()]
        return {"comparison": db.compare_recipe_costs(recipe_ids)}

    # =====================
    # ACHIEVEMENTS V2 (Feature 92)
    # =====================

    @app.post("/api/achievements", tags=["achievements"])
    def api_create_achievement(req: AchievementRequest):
        try:
            return {"success": True, **db.create_achievement(req.code, req.name, req.description, req.condition_type, req.condition_value)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/achievements/check", tags=["achievements"])
    def api_check_achievements(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        awarded = db.check_achievements(user.id)
        return {"newly_awarded": awarded}

    @app.get("/api/users/{user_id}/achievements", tags=["achievements"])
    def api_user_achievements(user_id: int):
        return {"achievements": db.get_user_achievements(user_id)}

    # =====================
    # HASHTAGS (Feature 93)
    # =====================

    @app.post("/api/recipes/{recipe_id}/hashtags", tags=["hashtags"])
    def api_add_hashtag(recipe_id: int, req: HashtagRequest, authorization: str | None = Header(None)):
        _get_user(authorization)
        return {"success": True, **db.add_hashtag(recipe_id, req.hashtag)}

    @app.delete("/api/recipes/{recipe_id}/hashtags/{hashtag}", tags=["hashtags"])
    def api_remove_hashtag(recipe_id: int, hashtag: str, authorization: str | None = Header(None)):
        _get_user(authorization)
        db.remove_hashtag(recipe_id, hashtag)
        return {"success": True}

    @app.get("/api/hashtags/{hashtag}/recipes", tags=["hashtags"])
    def api_hashtag_recipes(hashtag: str, limit: int = Query(50, ge=1, le=100)):
        recipes = db.search_by_hashtag(hashtag, limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    @app.get("/api/hashtags/trending", tags=["hashtags"])
    def api_trending_hashtags_2(limit: int = Query(10, ge=1, le=50)):
        return {"hashtags": db.get_trending_hashtags(limit=limit)}

    # =====================
    # PRICE ALERTS (Feature 94)
    # =====================

    @app.post("/api/price-alerts", tags=["alerts"])
    def api_set_price_alert(req: PriceAlertRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        alert = db.set_price_alert(user.id, req.ingredient, req.max_price)
        return {"success": True, "alert": {"ingredient": alert.ingredient, "max_price": alert.max_price}}

    @app.get("/api/price-alerts", tags=["alerts"])
    def api_get_price_alerts(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"alerts": [{"ingredient": a.ingredient, "max_price": a.max_price} for a in db.get_price_alerts(user.id)]}

    @app.get("/api/price-alerts/check", tags=["alerts"])
    def api_check_alerts(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"triggered": db.check_price_alerts(user.id)}

    # =====================
    # COLLABORATORS (Feature 95)
    # =====================

    @app.post("/api/recipes/{recipe_id}/collaborators", tags=["collab"])
    def api_invite_collab(recipe_id: int, req: CollaboratorRequest, authorization: str | None = Header(None)):
        _get_user(authorization)
        try:
            return {"success": True, **db.invite_collaborator(recipe_id, req.user_id, req.role)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/collaborators", tags=["collab"])
    def api_get_collabs(recipe_id: int):
        return {"collaborators": db.get_collaborators(recipe_id)}

    @app.delete("/api/recipes/{recipe_id}/collaborators/{user_id}", tags=["collab"])
    def api_remove_collab(recipe_id: int, user_id: int, authorization: str | None = Header(None)):
        _get_user(authorization)
        db.remove_collaborator(recipe_id, user_id)
        return {"success": True}

    # =====================
    # COOKING CLASSES (Feature 96)
    # =====================

    @app.post("/api/cooking-classes", tags=["classes"])
    def api_create_class(req: CookingClassRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        c = db.create_cooking_class(req.title, req.description, user.id, req.scheduled_date, req.max_participants)
        return {"success": True, "class": {"id": c.id, "title": c.title}}

    @app.post("/api/cooking-classes/{class_id}/join", tags=["classes"])
    def api_join_class(class_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        try:
            return {"success": True, **db.join_cooking_class(class_id, user.id)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/cooking-classes", tags=["classes"])
    def api_list_classes():
        classes = db.get_cooking_classes()
        return {"classes": [{"id": c.id, "title": c.title, "scheduled_date": c.scheduled_date} for c in classes]}

    # =====================
    # BUNDLES (Feature 97)
    # =====================

    @app.post("/api/bundles", tags=["bundles"])
    def api_create_bundle(req: BundleRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        b = db.create_bundle(user.id, req.name, req.description)
        return {"success": True, "bundle": {"id": b.id, "name": b.name}}

    @app.post("/api/bundles/{bundle_id}/recipes", tags=["bundles"])
    def api_add_to_bundle(bundle_id: int, req: BundleAddRequest):
        db.add_to_bundle(bundle_id, req.recipe_id, req.sort_order)
        return {"success": True}

    @app.get("/api/bundles/{bundle_id}/recipes", tags=["bundles"])
    def api_bundle_recipes(bundle_id: int):
        recipes = db.get_bundle_recipes(bundle_id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    @app.get("/api/bundles", tags=["bundles"])
    def api_list_bundles():
        bundles = db.get_bundles()
        return {"bundles": [{"id": b.id, "name": b.name, "description": b.description} for b in bundles]}

    # =====================
    # MEAL PREP (Feature 98)
    # =====================

    @app.post("/api/meal-preps", tags=["meal_prep"])
    def api_create_meal_prep(req: MealPrepRequest2, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        mp = db.create_meal_prep(user.id, req.name, req.prep_date, req.servings)
        return {"success": True, "meal_prep": {"id": mp.id, "name": mp.name}}

    @app.post("/api/meal-preps/{prep_id}/recipes/{recipe_id}", tags=["meal_prep"])
    def api_add_prep_recipe(prep_id: int, recipe_id: int, authorization: str | None = Header(None)):
        _get_user(authorization)
        db.add_meal_prep_recipe(prep_id, recipe_id)
        return {"success": True}

    @app.get("/api/meal-preps/{prep_id}/recipes", tags=["meal_prep"])
    def api_prep_recipes(prep_id: int):
        recipes = db.get_meal_prep_recipes(prep_id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    @app.get("/api/meal-preps", tags=["meal_prep"])
    def api_list_meal_preps(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        preps = db.get_user_meal_preps(user.id)
        return {"meal_preps": [{"id": p.id, "name": p.name, "prep_date": p.prep_date} for p in preps]}

    # =====================
    # ANALYTICS (Feature 99)
    # =====================

    @app.get("/api/recipes/{recipe_id}/analytics", tags=["analytics"])
    def api_recipe_analytics(recipe_id: int):
        try:
            return db.get_recipe_analytics(recipe_id)
        except ValueError as e:
            raise HTTPException(404, str(e))

    @app.get("/api/users/{user_id}/analytics", tags=["analytics"])
    def api_author_analytics(user_id: int):
        return db.get_author_analytics(user_id)

    # =====================
    # FLAVOR PROFILE (Feature 100)
    # =====================

    @app.put("/api/recipes/{recipe_id}/flavor", tags=["flavor"])
    def api_set_flavor(recipe_id: int, req: FlavorProfileRequest, authorization: str | None = Header(None)):
        _get_user(authorization)
        return db.set_flavor_profile(recipe_id, req.sweet, req.salty, req.sour, req.bitter, req.umami, req.spicy)

    @app.get("/api/recipes/{recipe_id}/flavor", tags=["flavor"])
    def api_get_flavor(recipe_id: int):
        f = db.get_flavor_profile(recipe_id)
        return {"flavor": f}

    @app.get("/api/flavor-search", tags=["flavor"])
    def api_flavor_search(flavor: str = Query(...), min_score: int = Query(3, ge=1, le=5), limit: int = Query(20, ge=1, le=100)):
        recipes = db.find_by_flavor(flavor, min_score, limit)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # APPROVAL QUEUE (Feature 101)
    # =====================

    @app.post("/api/recipes/{recipe_id}/submit-approval", tags=["approval"])
    def api_submit_approval(recipe_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        try:
            return {"success": True, **db.submit_for_approval(recipe_id, user.id)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/approvals/{recipe_id}/approve", tags=["approval"])
    def api_approve(recipe_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return db.approve_recipe_submission(recipe_id, user.id)

    @app.post("/api/approvals/{recipe_id}/reject", tags=["approval"])
    def api_reject(recipe_id: int, req: ApprovalRejectRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return db.reject_recipe_submission(recipe_id, user.id, req.reason)

    @app.get("/api/approvals/pending", tags=["approval"])
    def api_pending_approvals(limit: int = Query(50, ge=1, le=100)):
        return {"pending": db.get_pending_approvals(limit=limit)}

    # =====================
    # COOKING JOURNAL (Feature 102)
    # =====================

    @app.post("/api/journal", tags=["journal"])
    def api_add_journal(req: JournalRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        entry = db.add_journal_entry(user.id, req.date, req.content, req.recipe_id, req.mood)
        return {"success": True, "entry": {"id": entry.id, "date": entry.date}}

    @app.get("/api/journal", tags=["journal"])
    def api_get_journal(start: str | None = Query(None), end: str | None = Query(None),
                         limit: int = Query(50, ge=1, le=100), authorization: str | None = Header(None)):
        user = _get_user(authorization)
        entries = db.get_journal_entries(user.id, start, end, limit)
        return {"entries": [{"id": e.id, "date": e.date, "content": e.content, "mood": e.mood, "recipe_id": e.recipe_id} for e in entries]}

    # =====================
    # REMIX CHAIN (Feature 103)
    # =====================

    @app.get("/api/recipes/{recipe_id}/remix-chain", tags=["remix"])
    def api_remix_chain(recipe_id: int):
        return {"chain": db.get_remix_chain(recipe_id)}

    @app.get("/api/recipes/{recipe_id}/remix-tree", tags=["remix"])
    def api_remix_tree(recipe_id: int):
        return {"children": db.get_remix_tree(recipe_id)}

    # =====================
    # INGREDIENT PAIRING (Feature 104)
    # =====================

    @app.post("/api/ingredient-pairings", tags=["pairing"])
    def api_add_pairing(req: PairingRequest):
        return {"success": True, **db.add_ingredient_pairing(req.ingredient_a, req.ingredient_b, req.score)}

    @app.get("/api/ingredient-pairings/{ingredient}", tags=["pairing"])
    def api_get_pairings(ingredient: str, limit: int = Query(10, ge=1, le=50)):
        return {"pairings": db.get_pairings(ingredient, limit=limit)}

    @app.get("/api/recipes/{recipe_id}/suggest-pairings", tags=["pairing"])
    def api_suggest_pairings(recipe_id: int, limit: int = Query(5, ge=1, le=20)):
        return {"suggestions": db.suggest_pairings(recipe_id, limit=limit)}

    # =====================
    # MOOD TAGS (Feature 105)
    # =====================

    @app.put("/api/recipes/{recipe_id}/mood-tags", tags=["mood"])
    def api_set_moods(recipe_id: int, req: MoodTagsRequest, authorization: str | None = Header(None)):
        _get_user(authorization)
        return {"moods": db.set_mood_tags(recipe_id, req.moods)}

    @app.get("/api/recipes/{recipe_id}/mood-tags", tags=["mood"])
    def api_get_moods(recipe_id: int):
        return {"moods": db.get_mood_tags(recipe_id)}

    @app.get("/api/mood/{mood}/recipes", tags=["mood"])
    def api_mood_recipes(mood: str, limit: int = Query(50, ge=1, le=100)):
        recipes = db.find_by_mood(mood, limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # SPEED CHALLENGE (Feature 106)
    # =====================

    @app.post("/api/speed-challenges", tags=["speed"])
    def api_create_speed(req: SpeedChallengeRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"success": True, **db.create_speed_challenge(0, req.target_minutes)}

    @app.post("/api/speed-challenges/{challenge_id}/result", tags=["speed"])
    def api_submit_speed(challenge_id: int, req: SpeedResultRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        try:
            return {"success": True, **db.submit_speed_result(challenge_id, user.id, req.actual_minutes)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/speed-challenges/{challenge_id}/rankings", tags=["speed"])
    def api_speed_rankings(challenge_id: int):
        return {"rankings": db.get_speed_rankings(challenge_id)}

    # =====================
    # RECIPE GIFT (Feature 107)
    # =====================

    @app.post("/api/recipe-gifts", tags=["gifts"])
    def api_send_gift(req: GiftRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"success": True, **db.send_recipe_gift(user.id, req.recipient_id, req.recipe_id, req.message)}

    @app.get("/api/recipe-gifts/received", tags=["gifts"])
    def api_received_gifts(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"gifts": db.get_received_gifts(user.id)}

    @app.get("/api/recipe-gifts/sent", tags=["gifts"])
    def api_sent_gifts(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"gifts": db.get_sent_gifts(user.id)}

    @app.post("/api/recipe-gifts/{gift_id}/open", tags=["gifts"])
    def api_open_gift(gift_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        db.open_gift(gift_id, user.id)
        return {"success": True}

    # =====================
    # INGREDIENT WIKI (Feature 108)
    # =====================

    @app.post("/api/ingredient-wiki", tags=["wiki"])
    def api_add_wiki(req: IngredientInfoRequest):
        return {"success": True, **db.add_ingredient_info(req.name, req.description, req.tips, req.storage)}

    @app.get("/api/ingredient-wiki/{name}", tags=["wiki"])
    def api_get_wiki(name: str):
        info = db.get_ingredient_info(name)
        if not info:
            return {"info": None}
        return {"info": info}

    @app.get("/api/ingredient-wiki", tags=["wiki"])
    def api_search_wiki(q: str = Query(""), limit: int = Query(20, ge=1, le=100)):
        return {"results": db.search_ingredient_wiki(q, limit=limit)}

    # =====================
    # RECIPE CALENDAR (Feature 109)
    # =====================

    @app.get("/api/recipe-calendar", tags=["calendar"])
    def api_recipe_calendar(year: int = Query(...), month: int = Query(..., ge=1, le=12),
                             authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return db.get_recipe_calendar(user.id, year, month)

    # =====================
    # COOKING TECHNIQUES (Feature 110)
    # =====================

    @app.post("/api/techniques", tags=["techniques"])
    def api_add_technique(req: TechniqueRequest):
        try:
            return {"success": True, **db.add_technique(req.name, req.description, req.difficulty)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/techniques", tags=["techniques"])
    def api_list_techniques():
        return {"techniques": db.get_techniques()}

    @app.post("/api/recipes/{recipe_id}/techniques/{technique_id}", tags=["techniques"])
    def api_link_technique(recipe_id: int, technique_id: int):
        db.link_technique_to_recipe(recipe_id, technique_id)
        return {"success": True}

    @app.get("/api/recipes/{recipe_id}/techniques", tags=["techniques"])
    def api_recipe_techniques(recipe_id: int):
        return {"techniques": db.get_recipe_techniques(recipe_id)}

    # =====================
    # CHEF ENDORSEMENT (Feature 111)
    # =====================

    @app.post("/api/recipes/{recipe_id}/endorse", tags=["endorsement"])
    def api_endorse(recipe_id: int, req: EndorsementRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        try:
            return {"success": True, **db.endorse_recipe(user.id, recipe_id, req.comment)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/recipes/{recipe_id}/endorsements", tags=["endorsement"])
    def api_get_endorsements(recipe_id: int):
        return {"endorsements": db.get_endorsements(recipe_id)}

    @app.get("/api/endorsed-recipes", tags=["endorsement"])
    def api_endorsed_recipes(limit: int = Query(50, ge=1, le=100)):
        recipes = db.get_endorsed_recipes(limit=limit)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # INGREDIENT ORIGIN (Feature 112)
    # =====================

    @app.put("/api/ingredient-origins", tags=["origins"])
    def api_set_origin(req: OriginRequest):
        return {"success": True, **db.set_ingredient_origin(req.name, req.origin, req.description)}

    @app.get("/api/ingredient-origins/{name}", tags=["origins"])
    def api_get_origin(name: str):
        origin = db.get_ingredient_origin(name)
        return {"origin": origin}

    # =====================
    # EVENT RECIPES (Feature 113)
    # =====================

    @app.post("/api/events", tags=["events"])
    def api_create_event(req: EventRequest):
        return {"success": True, **db.create_event(req.name, req.event_date, req.description)}

    @app.post("/api/events/{event_id}/recipes/{recipe_id}", tags=["events"])
    def api_link_event_recipe(event_id: int, recipe_id: int):
        db.link_recipe_to_event(event_id, recipe_id)
        return {"success": True}

    @app.get("/api/events/{event_id}/recipes", tags=["events"])
    def api_event_recipes(event_id: int):
        recipes = db.get_event_recipes(event_id)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    @app.get("/api/events/upcoming", tags=["events"])
    def api_upcoming_events(limit: int = Query(10, ge=1, le=50)):
        return {"events": db.get_upcoming_events(limit=limit)}

    # =====================
    # GROUP COOK (Feature 114)
    # =====================

    @app.post("/api/group-cooks", tags=["group_cook"])
    def api_create_group_cook(req: GroupCookRequest, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return {"success": True, **db.create_group_cook(req.recipe_id, user.id, req.cook_date, req.max_participants)}

    @app.post("/api/group-cooks/{group_id}/join", tags=["group_cook"])
    def api_join_group(group_id: int, authorization: str | None = Header(None)):
        user = _get_user(authorization)
        try:
            return {"success": True, **db.join_group_cook(group_id, user.id)}
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/api/group-cooks", tags=["group_cook"])
    def api_list_groups():
        return {"groups": db.get_group_cooks()}

    @app.get("/api/group-cooks/{group_id}/members", tags=["group_cook"])
    def api_group_members(group_id: int):
        return {"members": db.get_group_members(group_id)}

    # =====================
    # NUTRITION MATCH (Feature 115)
    # =====================

    @app.get("/api/nutrition-match", tags=["nutrition"])
    def api_nutrition_match(calories: int | None = Query(None), protein: float | None = Query(None),
                             tolerance: float = Query(0.2, ge=0, le=1), limit: int = Query(20, ge=1, le=100)):
        recipes = db.find_nutrition_matching(calories, protein, tolerance, limit)
        return {"recipes": [_recipe_dict(r) for r in recipes]}

    # =====================
    # STORES (Feature 116)
    # =====================

    @app.post("/api/stores", tags=["stores"])
    def api_add_store(req: StoreRequest):
        return {"success": True, **db.add_store(req.name, req.location, req.description)}

    @app.post("/api/stores/{store_id}/ingredients", tags=["stores"])
    def api_link_store_ingredient(store_id: int, req: StoreIngredientRequest):
        return {"success": True, **db.link_ingredient_to_store(store_id, req.ingredient, req.price)}

    @app.get("/api/stores/ingredient/{ingredient}", tags=["stores"])
    def api_find_stores(ingredient: str):
        return {"stores": db.find_stores_for_ingredient(ingredient)}

    # =====================
    # RECIPE STORY (Feature 117)
    # =====================

    @app.put("/api/recipes/{recipe_id}/story", tags=["story"])
    def api_set_story(recipe_id: int, req: StoryRequest, authorization: str | None = Header(None)):
        _get_user(authorization)
        return db.set_recipe_story(recipe_id, req.story)

    @app.get("/api/recipes/{recipe_id}/story", tags=["story"])
    def api_get_story(recipe_id: int):
        story = db.get_recipe_story(recipe_id)
        return {"story": story}

    # =====================
    # COOKING FAQ (Feature 118)
    # =====================

    @app.post("/api/faqs", tags=["faq"])
    def api_add_faq(req: FaqRequest):
        return {"success": True, **db.add_faq(req.question, req.answer, req.category)}

    @app.get("/api/faqs", tags=["faq"])
    def api_get_faqs(category: str | None = Query(None), limit: int = Query(50, ge=1, le=100)):
        return {"faqs": db.get_faqs(category, limit=limit)}

    @app.get("/api/faqs/search", tags=["faq"])
    def api_search_faqs(q: str = Query(...), limit: int = Query(10, ge=1, le=50)):
        return {"faqs": db.search_faqs(q, limit=limit)}

    # =====================
    # RECIPE RANKINGS (Feature 119)
    # =====================

    @app.get("/api/recipe-rankings", tags=["rankings"])
    def api_rankings(category: str | None = Query(None), period: str = Query("all", pattern="^(all|week|month)$"),
                      limit: int = Query(20, ge=1, le=100)):
        return {"rankings": db.get_recipe_rankings(category, period, limit)}

    # =====================
    # WEEKLY DIGEST (Feature 120)
    # =====================

    @app.get("/api/weekly-digest", tags=["digest"])
    def api_weekly_digest(authorization: str | None = Header(None)):
        user = _get_user(authorization)
        return db.generate_weekly_digest(user.id)

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
            "category": recipe.category,
            "is_public": recipe.is_public,
            "scheduled_at": recipe.scheduled_at,
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
