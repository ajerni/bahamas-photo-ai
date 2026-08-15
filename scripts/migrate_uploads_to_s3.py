"""Upload local backend/local_data/uploads files into the configured S3 bucket.

Object keys stay trip_{id}/{filename}, matching stored_path in SQLite.
Run from the repo root after .env has PMM_S3_* set:

    .venv/bin/python scripts/migrate_uploads_to_s3.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.config import get_settings
from backend.app.services.storage import put_photo_bytes

UPLOADS = ROOT / "backend" / "local_data" / "uploads"
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def main() -> None:
    settings = get_settings()
    if not settings.s3_enabled:
        raise SystemExit(
            "S3 is not configured. Set PMM_S3_ENDPOINT, PMM_S3_BUCKET, "
            "PMM_S3_ACCESS_KEY, and PMM_S3_SECRET_KEY."
        )
    if not UPLOADS.is_dir():
        raise SystemExit(f"No local uploads directory at {UPLOADS}")

    files = [
        path
        for path in UPLOADS.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    ]
    if not files:
        print("No local photos to migrate.")
        return

    uploaded = 0
    for path in files:
        key = path.relative_to(UPLOADS).as_posix()
        mime = CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        put_photo_bytes(key, path.read_bytes(), mime, settings=settings)
        uploaded += 1
        print(f"uploaded {key}")

    print(f"Mirrored {uploaded} files to s3://{settings.s3_bucket}/")


if __name__ == "__main__":
    main()
