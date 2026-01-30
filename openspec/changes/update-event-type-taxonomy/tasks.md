## 1. Spec + validation
- [ ] 1.1 Add delta spec changes for `parse-api` (v2 taxonomy, `MISC_OTHER`, `v1_event_type`)
- [ ] 1.2 Run `openspec validate update-event-type-taxonomy --strict --no-interactive`

## 2. Implementation
- [ ] 2.1 Update `EventType` enum to v2 values
- [ ] 2.2 Add `v1_event_type` to response model and populate it
- [ ] 2.3 Update parser classification heuristics to emit v2 event types
- [ ] 2.4 Update `event_subtype` inference to remain consistent with v2 `event_type`

## 3. Tests + docs
- [ ] 3.1 Update unit tests to assert v2 event types
- [ ] 3.2 Update README and OpenSpec `parse-api` spec as needed
- [ ] 3.3 Ensure golden eval harness can still run (non-strict + strict modes)

## 4. Deploy
- [ ] 4.1 Redeploy Cloud Run
- [ ] 4.2 Smoke test 3–5 representative examples
