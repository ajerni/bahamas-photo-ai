"""Reset the local demo database and uploaded files."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA = ROOT / "backend" / "local_data"
DATABASE = LOCAL_DATA / "private_memory_map.db"
UPLOADS = LOCAL_DATA / "uploads"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Delete local app data without an interactive confirmation.",
    )
    args = parser.parse_args()

    if not args.yes:
        answer = input(
            "Delete backend/local_data/private_memory_map.db and uploads? "
            "Type RESET to continue: "
        )
        if answer != "RESET":
            print("Reset cancelled.")
            return

    if DATABASE.exists():
        DATABASE.unlink()
        print(f"Deleted {DATABASE.relative_to(ROOT)}")
    else:
        print(f"No database found at {DATABASE.relative_to(ROOT)}")

    if UPLOADS.exists():
        shutil.rmtree(UPLOADS)
        print(f"Deleted {UPLOADS.relative_to(ROOT)}")
    else:
        print(f"No uploads found at {UPLOADS.relative_to(ROOT)}")

    UPLOADS.mkdir(parents=True, exist_ok=True)
    print("Local data reset complete.")


if __name__ == "__main__":
    main()
