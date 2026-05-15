"""
Model management endpoints — list available LLMs and switch models.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx

from app.config import settings
from app.dependencies import get_current_user
from app.db.models.user import User

router = APIRouter()


class ModelInfo(BaseModel):
    name: str
    size: str | None = None
    modified_at: str | None = None
    family: str | None = None
    parameter_size: str | None = None


class ModelListResponse(BaseModel):
    models: list[ModelInfo]
    default_model: str


@router.get("/", response_model=ModelListResponse)
async def list_models(
    current_user: User = Depends(get_current_user),
):
    """
    List available LLM models from Ollama.

    Queries the Ollama API to get installed models.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [
                    ModelInfo(
                        name=m.get("name", ""),
                        size=_format_size(m.get("size", 0)),
                        modified_at=m.get("modified_at"),
                        family=m.get("details", {}).get("family"),
                        parameter_size=m.get("details", {}).get("parameter_size"),
                    )
                    for m in data.get("models", [])
                ]
                return ModelListResponse(
                    models=models,
                    default_model=settings.OLLAMA_DEFAULT_MODEL,
                )
    except httpx.ConnectError:
        pass  # Ollama not running — return empty list

    return ModelListResponse(
        models=[],
        default_model=settings.OLLAMA_DEFAULT_MODEL,
    )


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
