## Context
We want to "save and learn" from real user inputs without mutating parsing behavior online.

The approach is:
- log parse inputs/outputs (opt-in)
- accept structured feedback/corrections
- export feedback to JSONL to feed the existing eval harness

## Goals / Non-Goals
- Goals:
  - Persist parse requests/responses for debugging and offline learning.
  - Accept user corrections via a stable schema.
  - Export corrections into eval-compatible JSONL.
- Non-Goals:
  - Online learning that changes behavior immediately.
  - Building a full annotation UI.

## Decisions
### Decision: Storage backend
- Local/dev: SQLite
- Production: Postgres (Cloud SQL) or a managed alternative.

### Decision: Minimal schema
**Tables (conceptual):**
- `parse_runs`
  - `id` (uuid/int)
  - `created_at`
  - `source_url`, `source_name`, `source_published_at`
  - `text` (raw)
  - `response_json` (raw)
  - `schema_version`, `model_version`
- `feedback`
  - `id`
  - `created_at`
  - `parse_run_id` (nullable if client provides `input_id`)
  - `input_id` (nullable)
  - `corrected_fields_json`
  - `notes`

### Decision: Endpoint shape
- `POST /feedback`
  - Accepts either `parse_id` or `input_id`
  - Accepts optional corrected fields: `event_type`, `event_subtype`, `jurisdiction`, `assets`, `entities`, etc.
  - Returns a stable ack with feedback id.

### Decision: Export format
- Export script writes JSONL with objects shaped like:
  - `{ "id": "feedback-...", "text": "...", "expected": { ...corrected fields... } }`

### Decision: Security/auth
- In shared deployments, `POST /feedback` MUST require auth (API key) to prevent abuse.
- Rate limit feedback submissions.

### Decision: Privacy and retention
- Provide retention period configuration.
- Avoid storing additional PII; recommend redaction guidance in docs.

## Risks / Trade-offs
- Storage increases operational complexity for Cloud Run.
- Feedback can be low quality; exports should allow filtering (e.g., minimum confidence / reviewed flag) as future work.

## Migration Plan
- Start with disabled-by-default persistence.
- Add database only when the feature is enabled.
- Backfill/export tooling can be introduced independently.

## Open Questions
- Should we allow anonymous feedback in local dev but require auth in prod?
- Do we want a "reviewed" flag to separate curated training data from raw feedback?
