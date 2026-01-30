## Context
We currently expose a v1 `event_type` enum (ETF_*, enforcement, hacks, etc.) that is intentionally closed and limited. We also added `event_subtype` as a refinement field and a `misc` subtype catch-all for crypto-related UNKNOWNs.

We now want the MECE list to become the primary `event_type` taxonomy, and keep `event_subtype` as refinement.

## Goals / Non-Goals
- Goals:
  - Provide a more complete MECE primary taxonomy via `event_type`.
  - Preserve a safe fallback for crypto-related items via `MISC_OTHER`.
  - Preserve `UNKNOWN` for non-crypto or unclassifiable content.
  - Keep determinism guarantees in deterministic mode.
- Non-Goals:
  - Perfect classification of all categories in v2 (heuristics can start basic).
  - Changing jurisdiction taxonomy in this change.

## Decisions
- Decision: Introduce v2 taxonomy under the existing capability, signaled via `schema_version = "v2"`.
- Decision: Add `v1_event_type` as an optional response field for migration/debugging.
- Decision: Map legacy v1 categories to the closest v2 category where feasible; otherwise populate `v1_event_type` and fall back to `MISC_OTHER` / `UNKNOWN`.

## Risks / Trade-offs
- Risk: This is breaking for any client relying on v1 enum values.
  - Mitigation: `schema_version` bump + optional `v1_event_type`.
- Risk: Heuristic classifier may underfit new categories.
  - Mitigation: iterate using `eval/golden_cases.jsonl` and keep conservative fallback to `MISC_OTHER`.

## Migration Plan
1. Update response schema to v2 (`schema_version = "v2"`) and new `EventType` enum.
2. Keep producing a legacy mapping as `v1_event_type`.
3. Update tests + docs.
4. Redeploy and smoke test.

## Open Questions
- None (taxonomy list is sourced from the repo's golden set for initial v2).
