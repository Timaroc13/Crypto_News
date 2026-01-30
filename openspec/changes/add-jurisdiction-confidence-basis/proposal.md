# Change: Add Jurisdiction Confidence + Basis (Option A)

## Why
Today we collapse two distinct cases into `jurisdiction = "GLOBAL"`:
1) genuinely global events, and
2) geo-unstated/unclear events.

We want to keep the existing `Jurisdiction` enum stable (no `UNCLEAR_GEO` bucket) while still exposing whether geo was explicit vs inferred.

## What Changes
- Add two optional response fields:
  - `jurisdiction_confidence` (float 0..1)
  - `jurisdiction_basis` (string enum: `explicit` | `implied` | `none`)
- Keep `jurisdiction` as-is; continue defaulting to `GLOBAL` when geo is not explicit.

## Impact
- Affected spec: `parse-api`
- Affected code (planned): Pydantic response model, parser jurisdiction inference/scoring, tests, eval harness.
- Compatibility: additive, non-breaking (new fields optional).
