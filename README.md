# Private Memory Map

Private travel-memory workstation: import trip photos, map GPS pins from EXIF,
run a fixed vision workflow, browse memories, ask grounded questions, and export
a Markdown/ZIP dossier.

It is not a social app. Map coordinates come from EXIF/GPS only. The model can
describe visible scenes; it should not invent exact dates, events, or coordinates.

```text
Create a trip
  -> Import photos (skip duplicates)
  -> Review map and timeline
  -> Analyze photos (OpenRouter vision)
  -> Read generated memories
  -> Ask grounded questions
  -> Export a private dossier
```

Live: [https://bahamas.ernilabs.com](https://bahamas.ernilabs.com) (HTTP basic auth).

## Requirements

**Local**

- Python 3.12+
- Node.js 20+
- An [OpenRouter](https://openrouter.ai) API key (vision model, default `google/gemini-3.7-flash`)

**Live** (already running this way)

- VPS with Docker + Traefik on the external network `iotnetwork`
- DNS: `bahamas.ernilabs.com` → that VPS
- MinIO S3 API at `https://s3.wineagent.ch`, private bucket `bahamas`
- SQLite file on a Docker volume

Automated tests do not call the real model.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cd frontend
npm install
cd ..

cp .env.example .env
# set OPENROUTER_API_KEY in .env
```

Leave the `PMM_S3_*` keys empty for local disk storage under
`backend/local_data/uploads` and SQLite at
`backend/local_data/private_memory_map.db`.

If `PMM_S3_ENDPOINT`, `PMM_S3_BUCKET`, `PMM_S3_ACCESS_KEY`, and
`PMM_S3_SECRET_KEY` are all set, local runs write photos to MinIO instead.
Use the **S3 API host** (`https://s3.wineagent.ch`), not the MinIO console
(`https://minio.wineagent.ch`).

## Run locally

Backend (from the repo root):

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`. The Vite app talks to `http://localhost:8000`.
Analyze runs as an in-process background job; the UI polls until it finishes.

## Configuration

Copy [`.env.example`](.env.example). Common keys:

```text
OPENROUTER_API_KEY=
OPENROUTER_MODEL=google/gemini-3.7-flash

PMM_DATABASE_URL=sqlite:///backend/local_data/private_memory_map.db
PMM_UPLOAD_DIR=backend/local_data/uploads

PMM_S3_ENDPOINT=          # empty = local disk; live uses https://s3.wineagent.ch
PMM_S3_BUCKET=
PMM_S3_ACCESS_KEY=
PMM_S3_SECRET_KEY=

REVERSE_PROXY_USER=       # used live with PMM_ENABLE_BASIC_AUTH=true
REVERSE_PROXY_PASSWORD=

PMM_AUTO_ANALYZE_ON_IMPORT=true
PMM_WORKFLOW_MAX_IMAGE_EDGE_PX=1280
PMM_WORKFLOW_MAX_QA_PHOTOS=60
```

Frontend override (local Vite only; production build uses same-origin `/api`):

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Test

```bash
.venv/bin/python -m pytest backend/tests

cd frontend
npm run build
```

## Local demo utilities

```bash
.venv/bin/python scripts/reset_local_data.py --yes
.venv/bin/python scripts/seed_demo_trip.py
.venv/bin/python scripts/smoke_test_real_workflow.py /path/to/travel-photo.jpg
```

`seed_demo_trip.py --replace` recreates the seeded trip. The smoke script calls
the real OpenRouter model and is not part of CI.

Mirror local `backend/local_data/uploads/` into the configured S3 bucket
(keys stay `trip_{id}/{uuid}.ext`):

```bash
.venv/bin/python scripts/migrate_uploads_to_s3.py
```

## Live setup

Production is one Docker container behind existing Traefik.

| Piece | Where |
|---|---|
| Public URL | `https://bahamas.ernilabs.com` |
| TLS + HTTP→HTTPS | Traefik (`iotnetwork`, Let’s Encrypt) |
| App + SPA | image from [`Dockerfile`](Dockerfile), port 8000 |
| Auth | app HTTP basic auth (`REVERSE_PROXY_USER` / `REVERSE_PROXY_PASSWORD`) |
| Metadata DB | SQLite volume `bahamas_data` → `/data/private_memory_map.db` |
| Photos | MinIO bucket `bahamas` via `https://s3.wineagent.ch` (path-style S3) |
| Browser never talks to MinIO | FastAPI streams `/uploads/...` so basic auth covers originals |

Compose template: [`docker-compose.yml_example`](docker-compose.yml_example).
On the VPS that file is copied to `docker-compose.yml` (gitignored).

### What to upload

Upload source + `.env` + the SQLite file. **Do not** upload `uploads/`; photos
already live in MinIO.

Skip `.venv/`, `node_modules/`, and `frontend/dist/` (the image builds them).

```bash
# from this repo on your machine
rsync -avz \
  --exclude '.venv' --exclude 'node_modules' --exclude 'frontend/dist' \
  --exclude 'backend/local_data/uploads' \
  ./ user@vps:~/bahamas-photo-ai/
```

### On the VPS

```bash
cd ~/bahamas-photo-ai
cp docker-compose.yml_example docker-compose.yml
# confirm .env has PMM_S3_ENDPOINT=https://s3.wineagent.ch
docker compose up -d --build
docker cp backend/local_data/private_memory_map.db bahamas:/data/private_memory_map.db
docker restart bahamas
```

Open `https://bahamas.ernilabs.com` and sign in with the reverse-proxy user and
password.

## How analysis works

Python owns the sequence; the model only fills structured JSON at fixed steps:

1. Load photo records and stored image bytes (disk or S3).
2. Resize for the vision payload.
3. Photo analysis → validate → store.
4. Trip-level synthesis.
5. Grounded Q&A from stored analyses + trip memory.

Code: `backend/app/workflows/`.

## Repository layout

```text
backend/
  app/
    api/routes/       FastAPI routes (including GET /uploads)
    core/             settings, basic auth
    db/               SQLModel tables
    schemas/          request and response models
    services/         local disk or MinIO storage, EXIF, export
    workflows/        prompts, schemas, OpenRouter client
  tests/
frontend/             Vite + React SPA
scripts/              reset, seed, smoke test, S3 migrate
Dockerfile            multi-stage: SPA build + uvicorn
docker-compose.yml_example
```

Gitignored runtime data:

```text
backend/local_data/private_memory_map.db
backend/local_data/uploads/
.env
docker-compose.yml
```

## API

- `GET /api/health` (includes `"storage": "local"` or `"s3"`)
- `POST /api/trips`
- `GET /api/trips`
- `GET /api/trips/{trip_id}`
- `POST /api/trips/{trip_id}/photos`
- `POST /api/trips/{trip_id}/photos/import`
- `GET /api/trips/{trip_id}/photos`
- `PATCH /api/photos/{photo_id}`
- `DELETE /api/photos/{photo_id}`
- `POST /api/photos/{photo_id}/analyze`
- `POST /api/trips/{trip_id}/analyze`
- `DELETE /api/trips/{trip_id}/analysis`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/cancel`
- `POST /api/jobs/{job_id}/retry`
- `GET /api/trips/{trip_id}/jobs/latest`
- `POST /api/trips/{trip_id}/ask`
- `GET /api/trips/{trip_id}/questions`
- `PATCH /api/trips/{trip_id}`
- `DELETE /api/trips/{trip_id}`
- `GET /api/trips/{trip_id}/export.md`
- `GET /api/trips/{trip_id}/export.zip`
- `GET /uploads/{stored_path}` (photo bytes from disk or MinIO)

## License

MIT
