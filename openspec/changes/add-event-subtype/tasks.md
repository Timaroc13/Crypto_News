## 1. Spec
- [x] 1.1 Add delta requirements for `event_subtype` to parse-api spec
- [x] 1.2 Run `openspec validate add-event-subtype --strict --no-interactive`

## 2. Implementation
- [x] 2.1 Add `event_subtype: str | None` to ParseResponse (v1)
- [x] 2.2 Implement subtype inference rules in parser (best-effort, conservative)
- [x] 2.3 Ensure subtype does not change existing `event_type` behavior
- [x] 2.4 Add tests for a few representative subtypes
- [x] 2.5 Update docs/examples (Swagger/README if applicable)

## 3. Verification
- [x] 3.1 `pytest` passes
- [x] 3.2 `ruff` passes
