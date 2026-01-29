# Golden cases

Add **10–30** representative inputs to [golden_cases.jsonl](golden_cases.jsonl). One JSON object per line.

## JSONL format

Required:
- `id`: unique string
- `text`: input string
- `expected`: object (you can start minimal and expand later)

Optional metadata (not fetched, for traceability only):
- `source_url`
- `source_name`
- `source_published_at` (ISO 8601 string)

Recommended `expected` fields to start with:
- `event_type` (required)
- `jurisdiction`
- `sentiment`
- `assets` (list)
- `entities` (list)

Example:

```json
{"id":"sec-etf-inflow","source_url":"https://example.com/article","source_name":"Example","source_published_at":"2026-01-29T12:34:56Z","text":"...","expected":{"event_type":"ETF_INFLOW","jurisdiction":"US","assets":["BTC"],"sentiment":"positive"}}
```

## How it’s used

- `scripts/run_eval.py` runs the API parser directly and prints pass/fail.
- The test suite will **skip** golden checks if you haven’t populated at least one case beyond the default example.
