# Strategy

## Working Title

Building a Private Travel Memory Map with Local Gemma 4

## Core Teaching Point

A local multimodal model becomes more useful when it sits inside a small,
validated workflow. Python owns file handling, metadata extraction, persistence,
API contracts, background job progress, and schema validation. Gemma 4
contributes image understanding, trip synthesis, and grounded Q&A inside fixed
workflow steps.

This is not an agent demo. Gemma 4 does not choose tools or control execution.

```text
User uploads travel photos
  -> backend extracts EXIF metadata
  -> backend stores photo records locally
  -> user starts analysis
  -> background job runs fixed Gemma workflow
  -> photo memories and trip memory are stored
  -> user asks grounded questions with evidence photo IDs
```

## LLM Step Pattern

Every LLM step should keep three ingredients separate:

1. system instruction using `[Role]`, `[Task]`, `[Expected output]`, `[Rules]`;
2. prompt builder that assembles runtime context;
3. Pydantic output schema passed to Ollama structured output.

The current workflow has three Gemma checkpoints:

- photo memory analysis;
- trip memory synthesis;
- grounded trip Q&A.

Python may validate JSON, evidence IDs, file paths, and runtime limits. It
should avoid semantic heuristics such as keyword matching, tag counting, or
manual interest inference.

## MVP Promise

The user can upload photos from one trip and privately recover the shape of the
trip:

- where photos were taken when GPS metadata exists;
- when moments happened when EXIF timestamps exist;
- what each photo seems to show after Gemma analysis;
- what interests and themes recur across the trip;
- which photos support an answer to a trip question.

The app should never invent exact coordinates from image content. Map placement
comes from EXIF/GPS metadata only.

## Current Implementation

- FastAPI backend with SQLite, local image uploads, EXIF extraction, and
  background analysis jobs.
- React/Vite frontend with trip creation, upload, map, timeline, photo detail,
  trip synthesis, progress display, and grounded Q&A.
- Deterministic Gemma workflow under `backend/app/workflows/`.
- Reset-friendly local demo data under `backend/local_data/`.
