from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .llm_adapter import RefinementRequest, get_provider_from_env, stable_seed
from .fetch import (
    FetchBlockedError,
    FetchError,
    FetchTimeoutError,
    FetchTooLargeError,
    FetchUnsupportedContentTypeError,
    fetch_url_text,
)
from .models import (
    MAX_TEXT_LENGTH,
    ErrorEnvelope,
    ErrorObject,
    EventType,
    EventTypeV1,
    FeedbackRequest,
    FeedbackResponse,
    ParseRequest,
    ParseUrlRequest,
    ParseResponse,
)
from .parser import (
    CandidateEvent,
    extract_assets,
    extract_entities,
    infer_event_subtype,
    infer_sentiment,
    resolve_jurisdiction,
    resolve_jurisdiction_with_meta,
    select_primary_event,
)

from .storage import persistence_enabled, store_feedback, store_parse_run

SCHEMA_VERSION = "v2"
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
    low_confidence = (
        primary.event_type.value in {"UNKNOWN", "MISC_OTHER"}
    ) or (primary.confidence < 0.65)
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
    if request.method.upper() == "POST" and request.url.path in {"/parse", "/parse_url"}:
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
    response: Response = None,
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
    jurisdiction, jurisdiction_basis, jurisdiction_confidence = resolve_jurisdiction_with_meta(
        req.text
    )
    sentiment = infer_sentiment(req.text)

    primary, assets, entities = await _maybe_refine(req, primary, assets, entities)

    event_subtype = infer_event_subtype(req.text, primary.event_type)

    def infer_v1_event_type(text: str, event_type: EventType) -> EventTypeV1:
        t = text.lower()
        if (
            event_type
            in {
                EventType.NEW_PROTOCOL_PRODUCT_LAUNCHES,
                EventType.STABLECOINS_MONETARY_MECHANICS,
            }
            and "stablecoin" in t
        ):
            return EventTypeV1.STABLECOIN_ISSUANCE
        if event_type == EventType.REGULATORY_ACTION_ENFORCEMENT and any(
            w in t
            for w in [
                "lawsuit",
                "sues",
                "sued",
                "charges",
                "charged",
                "indict",
                "investigation",
                "probe",
            ]
        ) and any(r in t for r in ["sec", "cftc", "doj", "fca", "esma", "ofac"]):
            return EventTypeV1.ENFORCEMENT_ACTION
        if event_type == EventType.PROTOCOL_UPGRADES_NETWORK_CHANGES:
            return EventTypeV1.PROTOCOL_UPGRADE
        if event_type == EventType.SECURITY_INCIDENTS_EXPLOITS and any(
            w in t
            for w in [
                "exchange",
                "cex",
                "bybit",
                "coinbase",
                "binance",
                "kraken",
            ]
        ):
            return EventTypeV1.EXCHANGE_HACK
        if event_type in {EventType.UNKNOWN, EventType.MISC_OTHER}:
            return EventTypeV1.UNKNOWN
        return EventTypeV1.UNKNOWN

    # Topics are intentionally loose.
    topics: list[str] = []
    if primary.event_type in {
        EventType.REGULATORY_ACTION_ENFORCEMENT,
        EventType.LEGISLATION_POLICY_DEVELOPMENT,
        EventType.GOVERNMENT_CENTRAL_BANK_INITIATIVES,
    }:
        topics = ["REGULATION"]
    elif primary.event_type == EventType.STABLECOINS_MONETARY_MECHANICS:
        topics = ["STABLECOIN"]
    elif primary.event_type == EventType.NEW_PROTOCOL_PRODUCT_LAUNCHES:
        topics = ["LAUNCH"]
    elif primary.event_type == EventType.CAPITAL_MARKETS_ACTIVITY:
        topics = ["CAPITAL_MARKETS"]
    elif primary.event_type in {
        EventType.FUNDING_INVESTMENT_MA,
        EventType.INSTITUTIONAL_ADOPTION_STRATEGY,
    }:
        topics = ["INSTITUTIONS"]
    elif primary.event_type == EventType.MARKET_STRUCTURE_LIQUIDITY_SHIFTS:
        topics = ["MARKET_STRUCTURE"]
    elif primary.event_type == EventType.SECURITY_INCIDENTS_EXPLOITS:
        topics = ["SECURITY"]
    elif primary.event_type == EventType.INTEROPERABILITY_INFRA_DEVELOPMENTS:
        topics = ["INFRA"]
    elif primary.event_type == EventType.RWA_DEVELOPMENTS:
        topics = ["RWA"]
    elif primary.event_type == EventType.PAYMENTS_COMMERCE_CONSUMER_ADOPTION:
        topics = ["PAYMENTS"]

    parsed = ParseResponse(
        event_type=primary.event_type,
        v1_event_type=infer_v1_event_type(req.text, primary.event_type),
        event_subtype=event_subtype,
        topics=topics,
        assets=assets,
        entities=entities,
        jurisdiction=jurisdiction,
        jurisdiction_basis=jurisdiction_basis,
        jurisdiction_confidence=jurisdiction_confidence,
        sentiment=sentiment,
        impact_score=primary.impact_score,
        confidence=primary.confidence,
        schema_version=SCHEMA_VERSION,
        model_version=MODEL_VERSION,
    )

    if persistence_enabled():
        stored = store_parse_run(
            input_id=req.input_id,
            source_url=req.source_url,
            source_name=req.source_name,
            source_published_at=req.source_published_at,
            text=req.text,
            response=parsed.model_dump(),
        )
        if response is not None:
            response.headers["X-Parse-Id"] = str(stored.parse_id)

    return parsed


@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(
    req: FeedbackRequest,
    authorization: str | None = Header(default=None),
) -> FeedbackResponse:
    _require_api_key(authorization)

    if not persistence_enabled():
        raise HTTPException(
            status_code=400,
            detail=_error_payload(
                "PERSISTENCE_DISABLED",
                "Feedback is unavailable because persistence is disabled.",
            ),
        )

    if req.parse_id is None and not req.input_id:
        raise HTTPException(
            status_code=422,
            detail=_error_payload(
                "INVALID_REQUEST",
                "Provide either parse_id or input_id.",
                details={"fields": ["parse_id", "input_id"]},
            ),
        )

    try:
        fid = store_feedback(
            parse_id=req.parse_id,
            input_id=req.input_id,
            text=req.text,
            expected=req.expected,
            notes=req.notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=_error_payload("INVALID_REQUEST", str(e)),
        )

    return FeedbackResponse(feedback_id=fid)


@app.post("/parse_url", response_model=ParseResponse)
async def parse_url(
    req: ParseUrlRequest,
    authorization: str | None = Header(default=None),
    response: Response = None,
) -> ParseResponse:
    _require_api_key(authorization)

    try:
        fetched = await fetch_url_text(req.url)
    except FetchBlockedError as e:
        raise HTTPException(
            status_code=400,
            detail=_error_payload("URL_BLOCKED", str(e), details={"url": req.url}),
        )
    except FetchTooLargeError as e:
        raise HTTPException(
            status_code=413,
            detail=_error_payload("FETCH_TOO_LARGE", str(e), details={"url": req.url}),
        )
    except FetchTimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail=_error_payload("FETCH_TIMEOUT", str(e), details={"url": req.url}),
        )
    except FetchUnsupportedContentTypeError as e:
        raise HTTPException(
            status_code=415,
            detail=_error_payload("UNSUPPORTED_FETCH_CONTENT_TYPE", str(e), details={"url": req.url}),
        )
    except FetchError as e:
        raise HTTPException(
            status_code=502,
            detail=_error_payload("FETCH_FAILED", str(e), details={"url": req.url}),
        )

    # Reuse the main parse pipeline using extracted text.
    parse_req = ParseRequest(
        text=fetched.text,
        deterministic=req.deterministic,
        input_id=req.input_id,
        source_url=fetched.url,
        source_name=req.source_name,
        source_published_at=req.source_published_at,
    )
    return await parse(parse_req, authorization=authorization, response=response)
