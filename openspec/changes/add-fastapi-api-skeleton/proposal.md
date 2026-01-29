# Change: Add minimal FastAPI parse API skeleton

## Why
We need a minimal, low-cost v1 service that implements the PRD’s `POST /parse` contract with strict schema validity, `UNKNOWN` handling, and deterministic behavior support.

## What Changes
- Add a minimal FastAPI service with `POST /parse`.
- Add request/response models matching the PRD (including `UNKNOWN`, jurisdiction enum, error shape, version fields).
- Add a baseline deterministic heuristic parser as the default implementation.
- Add tests and lightweight tooling (ruff, pytest).

## Impact
- Affected specs: `parse-api` (new capability)
- Affected code: new Python service + models
- **Non-goals**: billing/overage mechanics, persistence/query endpoints, multi-event output (still single primary event)
