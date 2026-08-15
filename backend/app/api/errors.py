from __future__ import annotations

from fastapi import HTTPException, status


def workflow_bad_request(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )
