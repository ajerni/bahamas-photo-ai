from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response

from backend.app.core.config import get_settings
from backend.app.services.storage import ImageValidationError, read_photo_bytes

router = APIRouter(tags=["uploads"])

_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


@router.get("/{stored_path:path}")
def get_uploaded_photo(stored_path: str, request: Request) -> Response:
    del request
    suffix = f".{stored_path.rsplit('.', 1)[-1].lower()}" if "." in stored_path else ""
    try:
        content = read_photo_bytes(stored_path)
    except ImageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return Response(
        content=content,
        media_type=_CONTENT_TYPES.get(suffix, "application/octet-stream"),
        headers={"Cache-Control": "private, max-age=3600"},
    )
