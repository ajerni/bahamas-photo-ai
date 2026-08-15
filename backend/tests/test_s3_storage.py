from __future__ import annotations

from backend.app.core.config import get_settings
from backend.app.services import storage


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(self, Bucket: str, Key: str, Body: bytes, **kwargs) -> None:
        del Bucket, kwargs
        self.objects[Key] = Body

    def get_object(self, Bucket: str, Key: str) -> dict[str, object]:
        del Bucket
        if Key not in self.objects:
            raise _missing()
        return {"Body": _Body(self.objects[Key])}

    def head_object(self, Bucket: str, Key: str) -> dict[str, str]:
        del Bucket
        if Key not in self.objects:
            raise _missing()
        return {"Key": Key}

    def delete_object(self, Bucket: str, Key: str) -> None:
        del Bucket
        self.objects.pop(Key, None)

    def get_paginator(self, name: str):
        assert name == "list_objects_v2"
        client = self

        class Paginator:
            def paginate(self, Bucket: str, Prefix: str):
                del Bucket
                contents = [
                    {"Key": key} for key in client.objects if key.startswith(Prefix)
                ]
                yield {"Contents": contents}

        return Paginator()

    def delete_objects(self, Bucket: str, Delete: dict) -> None:
        del Bucket
        for item in Delete["Objects"]:
            self.objects.pop(item["Key"], None)


class _Body:
    def __init__(self, content: bytes) -> None:
        self._content = content

    def read(self) -> bytes:
        return self._content


class _Missing(Exception):
    response = {"Error": {"Code": "NoSuchKey"}}


def _missing() -> _Missing:
    return _Missing()


def test_s3_storage_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("PMM_DATABASE_URL", f"sqlite:///{(tmp_path / 's3.db').as_posix()}")
    monkeypatch.setenv("PMM_S3_ENDPOINT", "https://minio.example")
    monkeypatch.setenv("PMM_S3_BUCKET", "bahamas")
    monkeypatch.setenv("PMM_S3_ACCESS_KEY", "user")
    monkeypatch.setenv("PMM_S3_SECRET_KEY", "pass")
    get_settings.cache_clear()
    storage._cached_s3_client.cache_clear()

    fake = FakeS3()
    monkeypatch.setattr(storage, "_s3_client", lambda settings: fake)

    settings = get_settings()
    assert settings.s3_enabled is True
    assert settings.storage_kind == "s3"

    storage.put_photo_bytes("trip_1/a.jpg", b"jpeg-bytes", "image/jpeg", settings)
    assert fake.objects["trip_1/a.jpg"] == b"jpeg-bytes"
    assert storage.read_photo_bytes("trip_1/a.jpg", settings) == b"jpeg-bytes"
    assert storage.photo_exists("trip_1/a.jpg", settings) is True

    storage.delete_stored_photo("trip_1/a.jpg", settings)
    assert storage.photo_exists("trip_1/a.jpg", settings) is False

    storage.put_photo_bytes("trip_2/b.jpg", b"other", settings=settings)
    storage.delete_trip_upload_dir(2, settings)
    assert fake.objects == {}

    get_settings.cache_clear()
    storage._cached_s3_client.cache_clear()
