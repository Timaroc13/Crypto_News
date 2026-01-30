## 1. Specification
- [ ] 1.1 Define `feedback-api` capability spec delta (endpoints + schemas)
- [ ] 1.2 Define retention and security requirements (auth, redaction/PII guidance)

## 2. Implementation
- [ ] 2.1 Add storage schema (parses table, feedback table)
- [ ] 2.2 Add `POST /feedback` endpoint to submit corrections
- [ ] 2.3 Add export script to write JSONL suitable for eval harness

## 3. Validation
- [ ] 3.1 Add tests for persistence + feedback submission + export format
- [ ] 3.2 Run `pytest`
