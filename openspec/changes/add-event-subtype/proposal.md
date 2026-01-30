# Change: Add `event_subtype` to v1 ParseResponse

## Why
The v1 `event_type` enum is intentionally small and stable, but real-world crypto news contains many recurring subcategories (e.g., token listing, bankruptcy, bridge hack) that we want to surface without breaking clients by expanding the enum.

## What Changes
- Add an optional `event_subtype` field to the v1 response schema.
- Populate `event_subtype` from heuristics (and optionally LLM refinement later), while keeping `event_type` as the stable primary classification.
- Keep v1 backward compatible: existing clients that ignore unknown fields continue working.

## Impact
- Affected specs: `parse-api`
- Affected code: response model, parser pipeline, tests, and docs.
- Compatibility: **non-breaking** (new optional response field).
