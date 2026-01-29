# Project Context

## Purpose
This repo implements **Crypto News → Structured Signals API**: an API-first service that converts unstructured crypto-related text (articles, posts, press releases) into a **single canonical, schema-valid event object** suitable for deterministic downstream consumption.

Key goals (v1):

- Accept user-provided text only (no URL fetching, no aggregation)
- Produce **normalized JSON** with a closed v1 event taxonomy (plus `UNKNOWN` for no-match)
- Maintain strict schema validity (responses are always schema-safe)
- Support an optional deterministic mode for reproducibility

## Tech Stack
Current repo state is early-stage. Unless/until overridden, assume the following **recommended v1 stack** for an API + NLP/LLM pipeline:

- **Language**: Python 3.11+ (3.12 preferred)
- **Web framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **Schema/validation**: Pydantic v2 (single source of truth for request/response models)
- **Testing**: pytest
- **Lint/format**: ruff (format + lint)
- **Packaging**: uv or pip/venv (TBD)
- **LLM/NLP provider**: pluggable adapter (TBD: OpenAI / Azure OpenAI / local model)
- **Containerization**: Docker (optional but recommended for deploy parity)

If you already have a preferred stack (Node/TS, Go, etc.), update this section—OpenSpec should reflect what the project actually uses.

## Project Conventions

### Code Style
- **Naming**: `snake_case` for Python symbols, `PascalCase` for classes, uppercase for enums/tickers.
- **Formatting**: ruff formatter (black-compatible).
- **Typing**: prefer explicit types on public interfaces; keep Pydantic models typed.
- **Errors**: do not throw raw exceptions across the API boundary; always map to the documented error shape.

### Architecture Patterns
- **Layering** (recommended):
	- `api/` (FastAPI routes, request/response models)
	- `core/` (domain models/enums, pure utilities)
	- `pipeline/` (normalization → classification → extraction → scoring)
	- `providers/` (LLM/NLP adapters; no framework imports)
- **Purity & determinism**: pipeline stages should be deterministic given `(input_text, model_version, deterministic=true)`.
- **No side effects**: v1 parse endpoint should not require persistence; any logging/metrics are operational only.
- **Schema-first**: response is always schema-valid; uncertainty is represented by `confidence` and, if needed, `event_type="UNKNOWN"`.

### Testing Strategy
- **Unit tests**: per stage (normalization, extraction, scoring).
- **Schema contract tests**: validate every response against Pydantic model.
- **Golden tests**: a small corpus of representative texts with expected outputs for deterministic mode.
- **Edge cases**: empty text, oversize payload, non-English, multi-event text, no-match → `UNKNOWN`.

### Git Workflow
- Preferred: trunk-based development.
- Branches: `main` + short-lived `feature/*`.
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- PRs: required for changes touching schema, taxonomy, or selection logic.

## Domain Context
- Input is arbitrary crypto-related text; output is one canonical event.
- v1 extracts exactly one primary event; multi-event inputs select the highest-impact event.
- v1 taxonomy is closed; new event types require a version bump.
- Jurisdiction is conservative: infer only from explicit signals; otherwise `GLOBAL`.
- Topics are free-form strings in v1 (non-enforced).

## Important Constraints
- **Latency target**: p95 < 700ms (v1 prioritizes depth, but must be operable).
- **Schema validity**: 100%.
- **Security**: text-only input; do not fetch URLs; no code execution.
- **Determinism**: must be supported via request flag; responses include `schema_version` and `model_version`.

## External Dependencies
- **LLM/NLP provider** (TBD): used for classification/extraction when heuristic methods are insufficient.
- **Rate limiting/auth** (TBD implementation): API key auth, per-key limiting.
- Optional: observability stack (OpenTelemetry), error tracking (Sentry).
