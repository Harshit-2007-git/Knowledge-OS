"""
API v1 aggregate router.

Mounts all sub-routers under the /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.documents import router as documents_router
from app.api.v1.search import router as search_router
from app.api.v1.chat import router as chat_router
from app.api.v1.models import router as models_router
from app.api.v1.analytics import router as analytics_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(search_router, prefix="/search", tags=["Search"])
api_v1_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_v1_router.include_router(models_router, prefix="/models", tags=["Models"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
