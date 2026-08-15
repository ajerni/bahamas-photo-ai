from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.api.routes import analysis, ask, health, jobs, photos, trips, uploads
from backend.app.core.auth import BasicAuthMiddleware
from backend.app.core.config import get_settings
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_local_dirs()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_local_dirs()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(BasicAuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(trips.router, prefix=settings.api_prefix)
    app.include_router(photos.router, prefix=settings.api_prefix)
    app.include_router(analysis.router, prefix=settings.api_prefix)
    app.include_router(ask.router, prefix=settings.api_prefix)
    app.include_router(jobs.router, prefix=settings.api_prefix)
    app.include_router(uploads.router, prefix="/uploads")
    _mount_frontend(app, settings.frontend_dir)
    return app


def _mount_frontend(app: FastAPI, frontend_dir: Path) -> None:
    dist = frontend_dir.resolve()
    index = dist / "index.html"
    if not index.is_file():
        return

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("uploads/"):
            raise HTTPException(status_code=404)
        candidate = (dist / full_path).resolve()
        try:
            candidate.relative_to(dist)
        except ValueError as exc:
            raise HTTPException(status_code=404) from exc
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
