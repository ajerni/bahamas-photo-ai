from __future__ import annotations

from functools import lru_cache

from sqlmodel import Session, SQLModel, create_engine

from backend.app.core.config import get_settings
from backend.app.db.compat import ensure_sqlite_compat


@lru_cache
def get_engine():
    settings = get_settings()
    settings.ensure_local_dirs()
    connect_args = (
        {"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {}
    )
    return create_engine(settings.database_url, connect_args=connect_args)


def init_db() -> None:
    from backend.app.db import models  # noqa: F401

    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    ensure_sqlite_compat(engine)


def get_session():
    with Session(get_engine()) as session:
        yield session
