"""
Storage abstraction layer.

Switches between local disk and Supabase Storage depending on config.
"""

import logging
import uuid
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


async def save_file(content: bytes, workspace_id: str, ext: str) -> tuple[str, str]:
    """
    Persist uploaded bytes.
    Returns: (unique_filename, file_path_or_url)
    """
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    if settings.USE_SUPABASE_STORAGE:
        return await _save_to_supabase(content, workspace_id, unique_filename)
    else:
        return await _save_to_disk(content, workspace_id, unique_filename)


async def read_file(file_path: str) -> bytes:
    """Read file bytes from whichever backend stored it."""
    if settings.USE_SUPABASE_STORAGE and file_path.startswith("http"):
        return await _read_from_supabase(file_path)
    with open(file_path, "rb") as f:
        return f.read()


async def delete_file(file_path: str) -> None:
    """Delete a file from whichever backend stored it."""
    if settings.USE_SUPABASE_STORAGE and file_path.startswith("http"):
        await _delete_from_supabase(file_path)
    else:
        import os
        if os.path.exists(file_path):
            os.remove(file_path)


# ── Local Disk ────────────────────────────────────────────────────────────────

async def _save_to_disk(content: bytes, workspace_id: str, unique_filename: str) -> tuple[str, str]:
    workspace_upload_dir = Path(settings.UPLOAD_DIR).resolve() / workspace_id
    workspace_upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = workspace_upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(content)
    logger.info("Saved file to disk: %s", file_path)
    return unique_filename, file_path.absolute().as_posix()


# ── Supabase Storage ──────────────────────────────────────────────────────────

async def _save_to_supabase(content: bytes, workspace_id: str, unique_filename: str) -> tuple[str, str]:
    import httpx
    storage_path = f"{workspace_id}/{unique_filename}"
    upload_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object"
        f"/{settings.SUPABASE_STORAGE_BUCKET}/{storage_path}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            upload_url,
            content=content,
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/octet-stream",
                "x-upsert": "true",
            },
            timeout=60.0,
        )
        response.raise_for_status()
    public_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/public"
        f"/{settings.SUPABASE_STORAGE_BUCKET}/{storage_path}"
    )
    logger.info("Uploaded to Supabase Storage: %s", public_url)
    return unique_filename, public_url


async def _read_from_supabase(url: str) -> bytes:
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.content


async def _delete_from_supabase(url: str) -> None:
    import httpx
    try:
        marker = f"/object/public/{settings.SUPABASE_STORAGE_BUCKET}/"
        idx = url.find(marker)
        if idx == -1:
            logger.warning("Could not parse Supabase path from URL: %s", url)
            return
        storage_path = url[idx + len(marker):]
        delete_url = (
            f"{settings.SUPABASE_URL}/storage/v1/object"
            f"/{settings.SUPABASE_STORAGE_BUCKET}/{storage_path}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                delete_url,
                headers={"Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"},
                timeout=15.0,
            )
            response.raise_for_status()
    except Exception as e:
        logger.error("Failed to delete from Supabase Storage: %s", e)