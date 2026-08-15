"""Create a small local demo trip without calling Gemma."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.core.config import get_settings
from backend.app.db.models import (
    AnalysisJob,
    Photo,
    PhotoAnalysis,
    Trip,
    TripMemory,
    TripQuestion,
)
from backend.app.db.session import get_engine, init_db
from backend.app.services.storage import delete_trip_upload_dir

DEMO_TITLE = "Demo: Porto Weekend"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace any existing demo trip created by this script.",
    )
    args = parser.parse_args()

    settings = get_settings()
    settings.ensure_local_dirs()
    init_db()

    with Session(get_engine()) as session:
        existing = session.exec(select(Trip).where(Trip.title == DEMO_TITLE)).first()
        if existing is not None and not args.replace:
            print(f"Demo trip already exists with ID {existing.id}.")
            print("Run with --replace to recreate it.")
            return
        if existing is not None:
            _delete_trip(session, int(existing.id))

        trip = Trip(
            title=DEMO_TITLE,
            description="A seeded local demo with synthetic photos and saved memories.",
        )
        session.add(trip)
        session.commit()
        session.refresh(trip)

        photos = _create_demo_photos(session, int(trip.id), settings.upload_dir)
        trip.cover_photo_id = int(photos[0].id)
        session.add(trip)

        _create_demo_memory(session, int(trip.id), photos)
        session.commit()

        print(f"Created demo trip ID {trip.id}.")
        print("Open the frontend and select the demo trip from the sidebar.")


def _create_demo_photos(session: Session, trip_id: int, upload_dir: Path) -> list[Photo]:
    specs = [
        {
            "filename": "demo-river-walk.jpg",
            "color": "#4d8b91",
            "label": "River walk",
            "captured_at": datetime(2025, 5, 17, 10, 24),
            "latitude": 41.1404,
            "longitude": -8.6110,
            "caption": "Morning light along the river",
            "scene": "A quiet riverside walk with layered rooftops and water nearby.",
            "place_type": "riverside promenade",
            "mood": "calm",
            "activities": ["walking", "sightseeing"],
            "objects": ["river", "bridge", "rooftops"],
            "favorite": True,
        },
        {
            "filename": "demo-tile-corner.jpg",
            "color": "#3868a8",
            "label": "Tile corner",
            "captured_at": datetime(2025, 5, 17, 14, 8),
            "latitude": 41.1458,
            "longitude": -8.6102,
            "caption": "Blue tiles after lunch",
            "scene": "A tiled facade that turns an ordinary corner into a visual pause.",
            "place_type": "historic street",
            "mood": "curious",
            "activities": ["wandering", "photographing architecture"],
            "objects": ["tiles", "window", "stone wall"],
            "favorite": True,
        },
        {
            "filename": "demo-station-light.jpg",
            "color": "#c09243",
            "label": "Station light",
            "captured_at": datetime(2025, 5, 18, 9, 42),
            "latitude": 41.1456,
            "longitude": -8.6109,
            "caption": "A bright station pause",
            "scene": "A travel pause shaped by warm light, movement, and tiled walls.",
            "place_type": "train station",
            "mood": "bright",
            "activities": ["waiting", "transiting"],
            "objects": ["station", "tiles", "sunlight"],
            "favorite": False,
        },
    ]

    photos: list[Photo] = []
    trip_dir = upload_dir / f"trip_{trip_id}"
    trip_dir.mkdir(parents=True, exist_ok=True)

    for index, spec in enumerate(specs, start=1):
        image_name = f"{index:02d}-{spec['filename']}"
        path = trip_dir / image_name
        _write_demo_image(path, str(spec["color"]), str(spec["label"]))
        photo = Photo(
            trip_id=trip_id,
            filename=str(spec["filename"]),
            stored_path=f"trip_{trip_id}/{image_name}",
            byte_size=path.stat().st_size,
            mime_type="image/jpeg",
            captured_at=spec["captured_at"],
            latitude=spec["latitude"],
            longitude=spec["longitude"],
            exif_json={"demo": True},
            is_favorite=bool(spec["favorite"]),
        )
        session.add(photo)
        session.commit()
        session.refresh(photo)
        _store_demo_analysis(session, int(photo.id), spec)
        photos.append(photo)

    return photos


def _write_demo_image(path: Path, color: str, label: str) -> None:
    image = Image.new("RGB", (1280, 900), color=color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((70, 620, 1210, 830), fill=(255, 254, 250))
    draw.text((110, 675), label, fill=(24, 27, 31))
    draw.text((110, 730), "Synthetic local demo image", fill=(88, 94, 99))
    image.save(path, format="JPEG", quality=90)


def _store_demo_analysis(session: Session, photo_id: int, spec: dict[str, object]) -> None:
    payload = {
        "scene_summary": spec["scene"],
        "memory_caption": spec["caption"],
        "place_type": spec["place_type"],
        "visible_activities": spec["activities"],
        "visible_objects": spec["objects"],
        "sensory_details": ["warm light", "slow movement"],
        "inferred_interest_signals": ["architecture", "walkable streets"],
        "mood": spec["mood"],
        "uncertainty_notes": ["This is seeded demo content, not model output."],
        "confidence": 0.9,
    }
    session.add(
        PhotoAnalysis(
            photo_id=photo_id,
            scene=str(spec["scene"]),
            activities=list(spec["activities"]),
            objects=list(spec["objects"]),
            mood=str(spec["mood"]),
            memory_prompt=str(spec["caption"]),
            confidence=0.9,
            raw_model_json={
                "prompt_version": "demo-seed-v1",
                "photo_memory": payload,
            },
        )
    )
    session.commit()


def _create_demo_memory(session: Session, trip_id: int, photos: list[Photo]) -> None:
    photo_ids = [int(photo.id) for photo in photos]
    session.add(
        TripMemory(
            trip_id=trip_id,
            narrative_summary=(
                "This seeded trip reads like a slow Porto weekend: river views, "
                "blue tile details, and small pauses between walks."
            ),
            inferred_interests=["historic architecture", "quiet walks", "city texture"],
            recurring_themes=["tiles", "warm light", "unhurried movement"],
            memorable_moments=[
                {
                    "title": "Following the river",
                    "description": "The trip opens with water, rooftops, and a relaxed walk.",
                    "evidence_photo_ids": [photo_ids[0]],
                },
                {
                    "title": "Stopping for blue tiles",
                    "description": "The camera keeps returning to decorative street details.",
                    "evidence_photo_ids": [photo_ids[1], photo_ids[2]],
                },
            ],
            evidence_photo_ids=photo_ids,
            uncertainty_notes=["Demo memories are handcrafted seed data."],
            raw_model_json={"prompt_version": "demo-seed-v1"},
            prompt_version="demo-seed-v1",
        )
    )
    session.add(
        TripQuestion(
            trip_id=trip_id,
            question="What did I seem drawn to on this trip?",
            answer="You seemed drawn to walkable streets, decorative tiles, and soft city light.",
            evidence_photo_ids=photo_ids,
        )
    )


def _delete_trip(session: Session, trip_id: int) -> None:
    for photo in session.exec(select(Photo).where(Photo.trip_id == trip_id)).all():
        analysis = session.get(PhotoAnalysis, int(photo.id))
        if analysis is not None:
            session.delete(analysis)
        session.delete(photo)
    for memory in [session.get(TripMemory, trip_id)]:
        if memory is not None:
            session.delete(memory)
    for question in session.exec(
        select(TripQuestion).where(TripQuestion.trip_id == trip_id)
    ).all():
        session.delete(question)
    for job in session.exec(select(AnalysisJob).where(AnalysisJob.trip_id == trip_id)).all():
        session.delete(job)
    trip = session.get(Trip, trip_id)
    if trip is not None:
        session.delete(trip)
    session.commit()
    delete_trip_upload_dir(trip_id)


if __name__ == "__main__":
    main()
