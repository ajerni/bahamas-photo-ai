from __future__ import annotations

import json
from typing import Any

PROMPT_VERSION = "travel-memory-v1"

COMMON_RULES = """
You are the reasoning engine inside a deterministic local travel-memory workflow.
Do not call tools. Do not ask for actions. Return JSON only.
Use only the supplied image, metadata, and memory records.
Exact GPS coordinates, dates, and times may only come from supplied metadata.
Do not invent place names, dates, events, people, or coordinates.
If evidence is weak, say so in uncertainty_notes.
Evidence photo IDs must be selected only from the provided photo IDs.
""".strip()


def photo_analysis_system_instruction() -> str:
    return _system_instruction(
        role=(
            "You are a local multimodal travel-memory analyst. You inspect one "
            "travel photo and its metadata for a private memory app."
        ),
        task=(
            "Understand the visible scene, identify travel-relevant details, "
            "and describe what the photo may help the traveler remember."
        ),
        expected_output=(
            "Return exactly one JSON object matching the PhotoMemoryAnalysis "
            "schema: scene_summary, memory_caption, place_type, "
            "visible_activities, visible_objects, sensory_details, "
            "inferred_interest_signals, mood, uncertainty_notes, confidence."
        ),
    )


def trip_synthesis_system_instruction() -> str:
    return _system_instruction(
        role=(
            "You are a local trip-memory synthesizer. You read structured photo "
            "memories and summarize the trip without adding outside facts."
        ),
        task=(
            "Synthesize the trip narrative, recurring themes, inferred traveler "
            "interests, and memorable moments from provided photo analyses."
        ),
        expected_output=(
            "Return exactly one JSON object matching the TripMemorySynthesis "
            "schema: narrative_summary, inferred_interests, recurring_themes, "
            "memorable_moments, evidence_photo_ids, uncertainty_notes."
        ),
    )


def trip_question_system_instruction() -> str:
    return _system_instruction(
        role=(
            "You are a grounded local trip Q&A engine. You answer questions "
            "only from the supplied trip memory and photo-memory records."
        ),
        task=(
            "Answer the user's question and select evidence photo IDs from the "
            "provided allowed_photo_ids."
        ),
        expected_output=(
            "Return exactly one JSON object matching the GroundedTripAnswer "
            "schema: answer, evidence_photo_ids, uncertainty."
        ),
    )


def photo_analysis_prompt(photo_context: dict[str, Any]) -> str:
    return _sectioned_prompt(
        payload_name="Photo metadata",
        payload=photo_context,
    )


def trip_synthesis_prompt(trip_context: dict[str, Any]) -> str:
    return _sectioned_prompt(
        payload_name="Trip memory records",
        payload=trip_context,
    )


def trip_question_prompt(question_context: dict[str, Any]) -> str:
    return _sectioned_prompt(
        payload_name="Question context",
        payload=question_context,
    )


def retry_prompt(raw_response: str, validation_error: str) -> str:
    payload = {
        "invalid_response": raw_response[:4000],
        "validation_error": validation_error[:2000],
    }
    return _sectioned_prompt(
        payload_name="Validation failure",
        payload=payload,
    )


def _system_instruction(role: str, task: str, expected_output: str) -> str:
    return "\n\n".join(
        [
            f"[Role]\n{role}",
            f"[Task]\n{task}",
            f"[Expected output]\n{expected_output}",
            f"[Rules]\n{COMMON_RULES}",
        ]
    )


def _sectioned_prompt(payload_name: str, payload: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            f"[Prompt version]\n{PROMPT_VERSION}",
            f"[{payload_name}]\n{json.dumps(payload, indent=2, default=str)}",
        ]
    )
