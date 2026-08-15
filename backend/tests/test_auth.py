from __future__ import annotations

from fastapi.testclient import TestClient


def test_basic_auth_blocks_unauthenticated_requests(tmp_path, monkeypatch):
    client = _auth_client(tmp_path, monkeypatch)

    response = client.get("/api/health")

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")


def test_basic_auth_accepts_configured_credentials(tmp_path, monkeypatch):
    client = _auth_client(tmp_path, monkeypatch)

    response = client.get("/api/health", auth=("buernis", "secret"))

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def _auth_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("PMM_DATABASE_URL", f"sqlite:///{(tmp_path / 'auth.db').as_posix()}")
    monkeypatch.setenv("PMM_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("PMM_S3_ENDPOINT", "")
    monkeypatch.setenv("PMM_S3_BUCKET", "")
    monkeypatch.setenv("PMM_S3_ACCESS_KEY", "")
    monkeypatch.setenv("PMM_S3_SECRET_KEY", "")
    monkeypatch.setenv("PMM_ENABLE_BASIC_AUTH", "true")
    monkeypatch.setenv("REVERSE_PROXY_USER", "buernis")
    monkeypatch.setenv("REVERSE_PROXY_PASSWORD", "secret")
    monkeypatch.setenv("PMM_AUTO_ANALYZE_ON_IMPORT", "false")

    from backend.app.core.config import get_settings
    from backend.app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()

    from backend.app.main import create_app

    return TestClient(create_app())
