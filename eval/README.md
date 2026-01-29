# Golden cases

Add **10–30** representative inputs to [golden_cases.jsonl](golden_cases.jsonl).

## File format

Supported formats:

- **JSONL** (one JSON object per line)
- **JSON text sequence** (multiple JSON objects back-to-back; pretty-printed is OK)
- **JSON array** (a single `[...]` list of case objects)

Required:
- `id`: unique string
- `text`: input string
- `expected`: object (you can start minimal and expand later)

Optional metadata (not fetched, for traceability only):
- `source_url`
- `source_name`
- `source_published_at` (ISO 8601 string)

Recommended `expected` fields to start with:
- `event_type` (recommended)
- `jurisdiction`
- `sentiment`
- `assets` (list)
- `entities` (list)

Optional v1 mapping fields (recommended when your primary labels are nonstandard):
- `v1_event_type` (must match the v1 enum)
- `v1_jurisdiction` (must match the v1 enum)

Example:

```json
{"id":"sec-etf-inflow","source_url":"https://example.com/article","source_name":"Example","source_published_at":"2026-01-29T12:34:56Z","text":"...","expected":{"event_type":"ETF_INFLOW","jurisdiction":"US","assets":["BTC"],"sentiment":"positive"}}
```

## How it’s used

- `scripts/run_eval.py` runs the API parser directly and prints pass/fail.
- By default, **pytest treats golden cases as a smoke test** (requests must succeed, schema must be valid).
	- This lets you curate a richer dataset (including future taxonomy labels) without breaking CI.
- To enforce exact matching for all `expected` fields, run with `RUN_GOLDEN_STRICT=1`.
