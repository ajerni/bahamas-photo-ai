"""Run the real Gemma travel-memory workflow against one local image."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from sqlmodel import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.core.config import get_settings
from backend.app.db.models import Photo, Trip
from backend.app.db.session import get_engine, init_db
from backend.app.workflows.travel_memory import (
    analyze_photo_memory,
    answer_trip_question_with_gemma,
    synthesize_trip_memory,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", type=Path, help="Path to a local travel photo.")
    parser.add_argument(
        "--question",
        default="What does this trip seem to focus on?",
        help="Grounded Q&A prompt to ask after analysis.",
    )
    args = parser.parse_args()

    image_path = args.image_path.resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    settings = get_settings()
    settings.ensure_local_dirs()
    init_db()

    with Session(get_engine()) as session:
        trip = Trip(
            title="Real workflow smoke test",
            description="Created by scripts/smoke_test_real_workflow.py",
        )
        session.add(trip)
        session.commit()
        session.refresh(trip)

        relative_path = Path(f"trip_{trip.id}") / image_path.name
        destination = settings.upload_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, destination)

        photo = Photo(
            trip_id=int(trip.id),
            filename=image_path.name,
            stored_path=relative_path.as_posix(),
            exif_json={},
        )
        session.add(photo)
        session.commit()
        session.refresh(photo)

        print(f"Trip ID: {trip.id}")
        print(f"Photo ID: {photo.id}")
        print(f"Model: {settings.gemma_model}")

        analysis = analyze_photo_memory(session, int(photo.id))
        print("\nPhoto memory")
        print(f"- {analysis.memory_caption}")
        print(f"- {analysis.scene_summary}")

        memory = synthesize_trip_memory(session, int(trip.id))
        print("\nTrip memory")
        print(memory.narrative_summary)

        answer = answer_trip_question_with_gemma(session, int(trip.id), args.question)
        print("\nQ&A")
        print(answer.answer)
        print(f"Evidence photo IDs: {answer.evidence_photo_ids}")


if __name__ == "__main__":
    main()
