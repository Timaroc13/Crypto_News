## 1. Specification
- [x] 1.1 Define `feedback-api` capability spec delta (endpoints + schemas)
- [x] 1.2 Define retention and security requirements (auth, redaction/PII guidance)

## 2. Implementation
- [x] 2.1 Add storage schema (parses table, feedback table)
- [x] 2.2 Add `POST /feedback` endpoint to submit corrections
- [x] 2.3 Add export script to write JSONL suitable for eval harness

## 3. Validation
- [x] 3.1 Add tests for persistence + feedback submission + export format
- [x] 3.2 Run `pytest`
