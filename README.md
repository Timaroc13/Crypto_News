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
  - Body: `{ "text": "...", "deterministic": false }`
  - Returns a schema-valid response; returns `event_type="UNKNOWN"` when no v1 event matches.

## Environment

- `API_KEY` (optional): if set, requires `Authorization: Bearer <API_KEY>`
- `MODEL_VERSION` (optional): included in responses

## Deploy (Google Cloud Run)

Prereqs:

- `gcloud` installed
- A GCP project selected: `gcloud config set project <PROJECT_ID>`
- Artifact Registry enabled (recommended)

Build and deploy from this repo root:

```powershell
# Authenticate once
gcloud auth login

# Build and push (Cloud Build)
gcloud builds submit --tag gcr.io/<PROJECT_ID>/crypto-news-parser

# Deploy to Cloud Run (scale-to-zero by default)
gcloud run deploy crypto-news-parser `
  --image gcr.io/<PROJECT_ID>/crypto-news-parser `
  --region us-central1 `
  --allow-unauthenticated
```

To require an API key, set `API_KEY` as an environment variable in the Cloud Run service config.

## Golden evals

- Add 10–30 examples to [eval/golden_cases.jsonl](eval/golden_cases.jsonl)
- Run: `C:/dev/crypto-news-parser/.venv/Scripts/python.exe scripts/run_eval.py`
