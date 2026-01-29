# crypto-news-parser

API-first service that converts unstructured crypto-related text into a single canonical event object.

## Quickstart (local)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Run API
uvicorn crypto_news_parser.main:app --app-dir src --reload --port 8000
```

Test:

```powershell
pytest
```

## API

- `POST /parse`
  - Body: `{ "text": "...", "deterministic": false, "source_url": "https://..." }` (source URL is accepted as metadata only; it is not fetched)
  - Returns a schema-valid response; returns `event_type="UNKNOWN"` when no v1 event matches.

## Environment

- `API_KEY` (optional): if set, requires `Authorization: Bearer <API_KEY>`
- `MODEL_VERSION` (optional): included in responses

## Deploy (Google Cloud Run)

Prereqs:

- `gcloud` installed
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
