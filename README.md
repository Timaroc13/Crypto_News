# crypto-news-parser

API-first service that converts unstructured crypto-related text into a single canonical event object.

## Quickstart (local)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Optional: copy env template
Copy-Item .env.example .env

# Run API
uvicorn crypto_news_parser.main:app --app-dir src --reload --port 8000 --env-file .env
```

Test:

```powershell
pytest
```

## API

- `POST /parse`
  - Body: `{ "text": "...", "deterministic": false, "source_url": "https://..." }` (source URL is accepted as metadata only; it is not fetched)
  - Returns a schema-valid response (v2 taxonomy).
    - Uses `event_type="UNKNOWN"` for non-crypto or unclassifiable inputs.
    - Uses `event_type="MISC_OTHER"` for crypto-related inputs that don't map to a specific v2 category.
  - Response may include:
    - `event_subtype` (optional, implementation-defined, consistent with `event_type`).
      - Examples: `stablecoin.launch.registered`, `regulation.enforcement.lawsuit`, `protocol.upgrade.hard_fork`
    - `v1_event_type` (optional legacy mapping) for migration/debugging.

- `POST /parse_url`
  - Body: `{ "url": "https://...", "deterministic": false }`
  - Fetches the URL with SSRF protections and extracts readable text before parsing.

- `POST /feedback`
  - Body: `{ "parse_id": 123, "expected": { ... }, "notes": "..." }`
  - Or (when you don't have `parse_id`): `{ "input_id": "...", "text": "...", "expected": { ... } }`
  - Requires persistence enabled.

## Environment

- `API_KEY` (optional): if set, requires `Authorization: Bearer <API_KEY>`
- `MODEL_VERSION` (optional): included in responses
- `ENABLE_PERSISTENCE` (optional): set to `1` to store parse runs and accept feedback
- `DB_PATH` (optional): path to SQLite DB file (default: `./data.sqlite3`)

## Feedback export

When persistence is enabled and feedback has been collected, export eval-compatible JSONL:

```powershell
C:/dev/crypto-news-parser/.venv/Scripts/python.exe scripts/export_feedback.py --out eval/feedback_cases.jsonl
```

## Deploy (Google Cloud Run)

Prereqs:

- Google Cloud CLI (`gcloud`) installed: https://cloud.google.com/sdk/docs/install
- Authenticate + initialize once:
  - `gcloud init`
  - `gcloud auth login`
- A GCP project selected: `gcloud config set project <PROJECT_ID>`
- Artifact Registry enabled (recommended)

Recommended env vars:

- `MODEL_VERSION` (set to a release tag / commit SHA for traceability)
- `API_KEY` (optional; if set, requires `Authorization: Bearer <API_KEY>`)

Build and deploy from this repo root:

```powershell
# Authenticate once
gcloud auth login

# Recommended: use Artifact Registry
# One-liner deploy helper:
./scripts/deploy_cloud_run.ps1 -ProjectId <PROJECT_ID> -Region us-central1 -AllowUnauthenticated
```

Notes:

- The container reads `$env:PORT` on Cloud Run (defaults to 8080).
- For private services, omit `-AllowUnauthenticated`.
- For API keys, prefer Secret Manager and bind via `--set-secrets`.

## Golden evals

- Add 10–30 examples to [eval/golden_cases.jsonl](eval/golden_cases.jsonl)
- Run: `C:/dev/crypto-news-parser/.venv/Scripts/python.exe scripts/run_eval.py`
