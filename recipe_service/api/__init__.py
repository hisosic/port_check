"""FridgeChef API - FastAPI application."""

from __future__ import annotations

from typing import Any

from recipe_service.models import Database

# Global database instance
db = Database()


def get_db() -> Database:
    return db
