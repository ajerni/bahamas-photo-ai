from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "private_memory_map_test.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("PMM_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("PMM_UPLOAD_DIR", str(upload_dir))
    _disable_remote_storage(monkeypatch)
    # TestClient runs BackgroundTasks synchronously, so leaving this on would
    # make every import test hit the real model.
    monkeypatch.setenv("PMM_AUTO_ANALYZE_ON_IMPORT", "false")

    from backend.app.core.config import get_settings
    from backend.app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()

    from backend.app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()
    get_engine.cache_clear()


def _disable_remote_storage(monkeypatch) -> None:
    monkeypatch.setenv("PMM_S3_ENDPOINT", "")
    monkeypatch.setenv("PMM_S3_BUCKET", "")
    monkeypatch.setenv("PMM_S3_ACCESS_KEY", "")
    monkeypatch.setenv("PMM_S3_SECRET_KEY", "")
    monkeypatch.setenv("PMM_ENABLE_BASIC_AUTH", "false")
