from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .llm_adapter import RefinementRequest, get_provider_from_env, stable_seed
from .models import (
    MAX_TEXT_LENGTH,
    ErrorEnvelope,
    ErrorObject,
    ParseRequest,
    ParseResponse,
)
from .parser import (
    CandidateEvent,
    extract_assets,
    extract_entities,
    infer_sentiment,
    resolve_jurisdiction,
    select_primary_event,
)

SCHEMA_VERSION = "v1"
MODEL_VERSION = os.getenv("MODEL_VERSION", "news-parser-0.1")
REQUIRED_API_KEY = os.getenv("API_KEY")

app = FastAPI(title="Crypto News Parser", version=SCHEMA_VERSION)


def get_llm_provider():
    # Separated for test monkeypatching.
    return get_provider_from_env()


async def _maybe_refine(
    req: ParseRequest,
    primary: CandidateEvent,
    assets: list[str],
    entities: list[str],
) -> tuple[CandidateEvent, list[str], list[str]]:
    provider = get_llm_provider()
    if provider is None:
        return primary, assets, entities

    if req.deterministic and not getattr(provider, "supports_determinism", False):
        return primary, assets, entities

    # Refine only when the heuristic result is low-confidence.
    low_confidence = (primary.event_type.value == "UNKNOWN") or (primary.confidence < 0.65)
    if not low_confidence:
        return primary, assets, entities

    request = RefinementRequest(
        text=req.text,
        heuristic_event_type=primary.event_type,
        heuristic_confidence=primary.confidence,
        heuristic_assets=tuple(assets),
        heuristic_entities=tuple(entities),
        deterministic=req.deterministic,
        seed=stable_seed(req.text) if req.deterministic else None,
    )

    refinement = await provider.refine(request)

    new_primary = primary
    if refinement.event_type is not None:
        new_primary = CandidateEvent(
            event_type=refinement.event_type,
            confidence=primary.confidence,
            impact_score=primary.impact_score,
        )

    def merge(base: list[str], extra: list[str] | None) -> list[str]:
        if not extra:
            return base
        seen: set[str] = set(base)
        merged = list(base)
        for item in extra:
            if item not in seen:
                merged.append(item)
                seen.add(item)
        return merged

    new_assets = merge(assets, refinement.assets)
    new_entities = merge(entities, refinement.entities)
    return new_primary, new_assets, new_entities


@app.middleware("http")
async def enforce_json_content_type(request: Request, call_next):
    # Enforce JSON input (PRD: 415 for unsupported media type).
    # Do this in middleware so it runs before FastAPI attempts to parse/validate the body.
    if request.method.upper() == "POST" and request.url.path == "/parse":
        content_type = request.headers.get("content-type")
        if content_type is not None:
            ct = content_type.split(";", 1)[0].strip().lower()
            if ct not in {"application/json"} and not ct.endswith("+json"):
                return _error(
                    code="UNSUPPORTED_MEDIA_TYPE",
                    message="Content-Type must be application/json.",
                    status=415,
                    details={"content_type": content_type},
                )
    return await call_next(request)


def _error_payload(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    envelope = ErrorEnvelope(error=ErrorObject(code=code, message=message, details=details or {}))
    return envelope.model_dump()


def _error(
    code: str,
    message: str,
    status: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(status_code=status, content=_error_payload(code, message, details))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    # Ensure JSON-serializable: FastAPI may include raw Exception objects in ctx.
    for err in errors:
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and isinstance(ctx.get("error"), Exception):
            ctx["error"] = str(ctx["error"])
        # FastAPI can include raw bytes in 'input' for non-JSON bodies.
        if isinstance(err.get("input"), (bytes, bytearray)):
            err["input"] = (err["input"][:200]).decode("utf-8", errors="replace")

    # FastAPI uses RequestValidationError for invalid JSON too; map that to 400 per PRD.
    if any(err.get("type") == "json_invalid" for err in errors):
        return _error(
            code="INVALID_JSON",
            message="Invalid JSON.",
            status=400,
            details={"errors": errors},
        )
    return _error(
        code="INVALID_REQUEST",
        message="Request validation failed.",
        status=422,
        details={"errors": errors},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    # Preserve our documented error envelope.
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return _error(code="HTTP_ERROR", message=str(exc.detail), status=exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    return _error(code="INTERNAL_ERROR", message="Internal server error.", status=500)


def _require_api_key(authorization: str | None) -> None:
    if not REQUIRED_API_KEY:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail=_error_payload("UNAUTHORIZED", "Missing API key."),
        )
    token = authorization.split(" ", 1)[1].strip()
    if token != REQUIRED_API_KEY:
        raise HTTPException(status_code=403, detail=_error_payload("FORBIDDEN", "Invalid API key."))


@app.post("/parse", response_model=ParseResponse)
async def parse(
    req: ParseRequest,
    authorization: str | None = Header(default=None),
) -> ParseResponse:
    _require_api_key(authorization)

    # Enforce max length here too (validator covers most cases; this makes it explicit).
    if len(req.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=_error_payload(
                code="PAYLOAD_TOO_LARGE",
                message=f"text exceeds max length {MAX_TEXT_LENGTH}",
                details={"max_length": MAX_TEXT_LENGTH},
            ),
        )

    primary = select_primary_event(req.text)
    assets = extract_assets(req.text)
    entities = extract_entities(req.text)
    jurisdiction = resolve_jurisdiction(req.text)
    sentiment = infer_sentiment(req.text)

    primary, assets, entities = await _maybe_refine(req, primary, assets, entities)

    # Topics are intentionally loose in v1.
    topics = []
    if primary.event_type.value.startswith("ETF_"):
        topics = ["ETF", "REGULATION"]
    elif primary.event_type.value in {"EXCHANGE_HACK", "ENFORCEMENT_ACTION"}:
        topics = ["RISK"]

    return ParseResponse(
        event_type=primary.event_type,
        topics=topics,
        assets=assets,
        entities=entities,
        jurisdiction=jurisdiction,
        sentiment=sentiment,
        impact_score=primary.impact_score,
        confidence=primary.confidence,
        schema_version=SCHEMA_VERSION,
        model_version=MODEL_VERSION,
    )
