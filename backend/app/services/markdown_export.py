from __future__ import annotations

import re
from datetime import datetime
from html import escape
from io import BytesIO
from json import dumps
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from backend.app.db.models import Photo, Trip, TripMemory, TripQuestion
from backend.app.services.storage import stored_photo_path


def trip_markdown(
    trip: Trip,
    photos: list[Photo],
    memory: TripMemory | None,
    questions: list[TripQuestion] | None = None,
) -> str:
    lines = [
        f"# {trip.title}",
        "",
    ]
    if trip.description:
        lines.extend([trip.description, ""])

    if memory is not None:
        summary = memory.user_narrative_summary or memory.narrative_summary
        if summary:
            lines.extend(["## Trip Story", "", summary, ""])
        if memory.user_note:
            lines.extend(["## Personal Note", "", memory.user_note, ""])
        lines.extend(_list_section("Inferred Interests", memory.inferred_interests))
        lines.extend(_list_section("Recurring Themes", memory.recurring_themes))
        if memory.memorable_moments:
            lines.extend(["## Memorable Moments", ""])
            for moment in memory.memorable_moments:
                title = str(moment.get("title") or "Moment")
                description = str(moment.get("description") or "")
                evidence = _ids(moment.get("evidence_photo_ids"))
                lines.extend([f"### {title}", ""])
                if description:
                    lines.extend([description, ""])
                if evidence:
                    lines.extend([f"Evidence photos: {_id_list(evidence)}", ""])
        lines.extend(_list_section("Uncertainty Notes", memory.uncertainty_notes))

    favorites = [photo for photo in photos if photo.is_favorite]
    if favorites:
        lines.extend(["## Kept Photos", ""])
        for photo in favorites:
            lines.append(f"- #{photo.id} {photo.filename}")
        lines.append("")

    if photos:
        lines.extend(["## Photo Memories", ""])
        for photo in photos:
            lines.extend(_photo_lines(photo))

    if questions:
        lines.extend(["## Questions", ""])
        for question in questions:
            lines.extend([f"### {question.question}", "", question.answer, ""])
            if question.evidence_photo_ids:
                lines.extend(
                    [f"Evidence photos: {_id_list(question.evidence_photo_ids)}", ""]
                )

    return "\n".join(lines).strip() + "\n"


def export_filename(title: str) -> str:
    slug = _slug(title)
    return f"{slug or 'trip-memory'}.md"


def export_zip_filename(title: str) -> str:
    slug = _slug(title)
    return f"{slug or 'trip-memory'}-dossier.zip"


def trip_zip_bytes(
    trip: Trip,
    photos: list[Photo],
    memory: TripMemory | None,
    questions: list[TripQuestion],
) -> bytes:
    photo_names = {int(photo.id): _archive_photo_name(photo) for photo in photos}
    payload = BytesIO()
    with ZipFile(payload, "w", ZIP_DEFLATED) as archive:
        archive.writestr("memory.md", trip_markdown(trip, photos, memory, questions))
        archive.writestr("metadata.json", _metadata_json(trip, photos, memory, questions))
        archive.writestr(
            "index.html",
            _html_dossier(trip, photos, memory, questions, photo_names),
        )
        for photo in photos:
            path = stored_photo_path(photo.stored_path)
            if path.exists():
                archive.write(path, f"photos/{photo_names[int(photo.id)]}")
    return payload.getvalue()


def _photo_lines(photo: Photo) -> list[str]:
    analysis = photo.analysis
    title = analysis.memory_caption if analysis is not None else photo.filename
    lines = [f"### #{photo.id} {title}", ""]
    lines.append(f"- File: {photo.filename}")
    if photo.is_favorite:
        lines.append("- Kept: yes")
    if photo.captured_at:
        lines.append(f"- Captured: {_format_datetime(photo.captured_at)}")
    if photo.latitude is not None and photo.longitude is not None:
        lines.append(f"- GPS: {photo.latitude}, {photo.longitude}")
    if analysis is not None:
        if analysis.scene_summary:
            lines.append(f"- Scene: {analysis.scene_summary}")
        mood = analysis.user_mood or analysis.mood
        if mood:
            lines.append(f"- Mood: {mood}")
        if analysis.place_type:
            lines.append(f"- Place type: {analysis.place_type}")
        if analysis.user_note:
            lines.extend(["", analysis.user_note])
    lines.append("")
    return lines


def _metadata_json(
    trip: Trip,
    photos: list[Photo],
    memory: TripMemory | None,
    questions: list[TripQuestion],
) -> str:
    return dumps(
        {
            "trip": {
                "id": trip.id,
                "title": trip.title,
                "description": trip.description,
                "cover_photo_id": trip.cover_photo_id,
                "created_at": trip.created_at.isoformat(),
            },
            "memory": None
            if memory is None
            else {
                "narrative_summary": memory.user_narrative_summary
                or memory.narrative_summary,
                "inferred_interests": memory.inferred_interests,
                "recurring_themes": memory.recurring_themes,
                "memorable_moments": memory.memorable_moments,
                "evidence_photo_ids": memory.evidence_photo_ids,
                "uncertainty_notes": memory.uncertainty_notes,
                "user_note": memory.user_note,
            },
            "photos": [
                {
                    "id": photo.id,
                    "filename": photo.filename,
                    "captured_at": photo.captured_at.isoformat()
                    if photo.captured_at
                    else None,
                    "latitude": photo.latitude,
                    "longitude": photo.longitude,
                    "is_favorite": photo.is_favorite,
                    "content_sha256": photo.content_sha256,
                    "analysis": None
                    if photo.analysis is None
                    else {
                        "caption": photo.analysis.memory_caption,
                        "scene": photo.analysis.scene_summary,
                        "mood": photo.analysis.user_mood or photo.analysis.mood,
                        "place_type": photo.analysis.place_type,
                        "uncertainty_notes": photo.analysis.uncertainty_notes,
                        "user_note": photo.analysis.user_note,
                    },
                }
                for photo in photos
            ],
            "questions": [
                {
                    "id": question.id,
                    "question": question.question,
                    "answer": question.answer,
                    "evidence_photo_ids": question.evidence_photo_ids,
                    "created_at": question.created_at.isoformat(),
                }
                for question in questions
            ],
        },
        indent=2,
    )


def _html_dossier(
    trip: Trip,
    photos: list[Photo],
    memory: TripMemory | None,
    questions: list[TripQuestion],
    photo_names: dict[int, str],
) -> str:
    summary = ""
    if memory is not None:
        summary = memory.user_narrative_summary or memory.narrative_summary
    sections = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{escape(trip.title)} Dossier</title>",
        "<style>",
        "body{margin:0;background:#f5f5f1;color:#181b1f;font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}",
        "main{max-width:980px;margin:0 auto;padding:40px 22px 72px}",
        "header{border-bottom:1px solid #d8d9d2;margin-bottom:28px;padding-bottom:22px}",
        "h1{font-size:clamp(2rem,6vw,4.5rem);line-height:1;margin:0 0 12px}",
        "h2{margin:34px 0 12px}.meta,.muted{color:#687078}",
        ".grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}",
        "figure{background:#fffefa;border:1px solid #d8d9d2;margin:0;padding:10px;box-shadow:0 14px 34px #181b1f14}",
        "img{max-width:100%;display:block}figcaption{padding:10px 2px 2px;font-weight:700}",
        "article{border-top:1px solid #d8d9d2;padding:16px 0}",
        "</style>",
        "</head>",
        "<body><main>",
        "<header>",
        f"<p class='meta'>Private Memory Map export</p><h1>{escape(trip.title)}</h1>",
    ]
    if trip.description:
        sections.append(f"<p>{escape(trip.description)}</p>")
    sections.append("</header>")

    if summary:
        sections.extend(["<section><h2>Trip Story</h2>", f"<p>{escape(summary)}</p>"])
        if memory is not None and memory.user_note:
            sections.append(f"<p><strong>Private note:</strong> {escape(memory.user_note)}</p>")
        if memory is not None and memory.memorable_moments:
            sections.append("<h2>Memorable Moments</h2>")
            for moment in memory.memorable_moments:
                title = escape(str(moment.get("title") or "Moment"))
                description = escape(str(moment.get("description") or ""))
                evidence = _id_list(_ids(moment.get("evidence_photo_ids")))
                sections.append(f"<article><h3>{title}</h3><p>{description}</p>")
                if evidence:
                    sections.append(f"<p class='muted'>Evidence photos: {escape(evidence)}</p>")
                sections.append("</article>")
        sections.append("</section>")

    if photos:
        sections.append("<section><h2>Timeline</h2>")
        for photo in photos:
            analysis = photo.analysis
            title = analysis.memory_caption if analysis is not None else photo.filename
            timestamp = photo.captured_at or photo.created_at
            sections.append("<article>")
            sections.append(f"<h3>#{photo.id} {escape(title)}</h3>")
            sections.append(f"<p class='muted'>{escape(_format_datetime(timestamp))}</p>")
            if photo.latitude is not None and photo.longitude is not None:
                sections.append(f"<p>GPS: {photo.latitude}, {photo.longitude}</p>")
            if analysis is not None:
                sections.append(f"<p>{escape(analysis.scene_summary)}</p>")
                if analysis.user_note:
                    sections.append(f"<p><strong>Note:</strong> {escape(analysis.user_note)}</p>")
            sections.append("</article>")
        sections.append("</section><section><h2>Photo Archive</h2><div class='grid'>")
        for photo in photos:
            archive_name = photo_names.get(int(photo.id), "")
            analysis = photo.analysis
            title = analysis.memory_caption if analysis is not None else photo.filename
            sections.extend(
                [
                    "<figure>",
                    f"<img src='photos/{escape(archive_name)}' alt=''>",
                    f"<figcaption>#{photo.id} {escape(title)}</figcaption>",
                    "</figure>",
                ]
            )
        sections.append("</div></section>")

    if questions:
        sections.append("<section><h2>Questions</h2>")
        for question in questions:
            sections.append(
                f"<article><h3>{escape(question.question)}</h3><p>{escape(question.answer)}</p>"
            )
            if question.evidence_photo_ids:
                sections.append(
                    f"<p class='muted'>Evidence photos: {escape(_id_list(question.evidence_photo_ids))}</p>"
                )
            sections.append("</article>")
        sections.append("</section>")

    sections.append("</main></body></html>")
    return "\n".join(sections)


def _archive_photo_name(photo: Photo) -> str:
    return f"{photo.id}-{Path(photo.filename).name or 'photo'}"


def _list_section(title: str, values: list[str]) -> list[str]:
    if not values:
        return []
    return [f"## {title}", "", *[f"- {value}" for value in values], ""]


def _ids(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    return [int(item) for item in value if isinstance(item, int)]


def _id_list(values: list[int]) -> str:
    return ", ".join(f"#{value}" for value in values)


def _format_datetime(value: datetime) -> str:
    return value.isoformat()


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
