# TODO

This file mirrors the active development TODO list tracked in chat.

## Next milestones

- [ ] Normalize golden event labels
  - Add a second field like `expected.v1_event_type` (or update `expected.event_type`) to match the v1 enum in `src/crypto_news_parser/models.py`.
  - Keep richer/nonstandard labels as-is for now, but capture the v1 mapping for 10–30 cases.

- [ ] Improve taxonomy coverage
  - Extend `src/crypto_news_parser/parser.py` heuristics to correctly classify v1 event types using golden cases as targets.
  - Focus on the top 5–7 most frequent categories first; keep `UNKNOWN` fallback.

- [ ] Jurisdiction extraction pass
  - Improve `resolve_jurisdiction()` to catch explicit non-US signals (e.g., UAE, Hong Kong) while following PRD rule: only explicit references; otherwise `GLOBAL`.

- [ ] Entity extraction baseline
  - Add a conservative entity extractor (regex/heuristics) for proper nouns; add a few tests.

- [ ] Assets extraction improvements
  - Tighten ticker detection (BTC/ETH/SOL/etc), reduce false positives; add golden expectations for a subset.

- [ ] Add LLM adapter interface
  - Add a provider interface (no provider by default) to optionally refine outputs when heuristic confidence is low.
  - Ensure deterministic mode pins prompt/template version.

- [ ] CI workflow
  - Add GitHub Actions to run pytest + ruff on PRs/pushes.

- [ ] Cloud Run deploy hardening
  - Improve deploy docs + env var guidance; optional `gcloud` deploy script.

- [ ] OpenSpec archive after deploy
  - After first deploy, archive `openspec/changes/add-fastapi-api-skeleton` into `openspec/changes/archive/...` and validate.
