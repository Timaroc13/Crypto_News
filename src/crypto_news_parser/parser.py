from __future__ import annotations

import re
from dataclasses import dataclass

from .models import EventType, Jurisdiction, Sentiment


@dataclass(frozen=True)
class CandidateEvent:
    event_type: EventType
    confidence: float
    impact_score: float


_PRECEDENCE: dict[EventType, int] = {
    EventType.EXCHANGE_HACK: 1,
    EventType.ENFORCEMENT_ACTION: 2,
    EventType.STABLECOIN_DEPEG: 3,
    EventType.ETF_APPROVAL: 4,
    EventType.ETF_REJECTION: 4,
    EventType.ETF_INFLOW: 5,
    EventType.ETF_OUTFLOW: 5,
    EventType.ETF_FILING: 6,
    EventType.PROTOCOL_UPGRADE: 7,
    EventType.STABLECOIN_ISSUANCE: 8,
    EventType.CEX_INFLOW: 9,
    EventType.CEX_OUTFLOW: 9,
    EventType.MINER_SHUTDOWN: 10,
    EventType.UNKNOWN: 11,
}


_TICKER_RE = re.compile(r"(?:\$)?([A-Z]{2,6})\b")


def extract_assets(text: str) -> list[str]:
    # Best-effort: capture likely tickers; filter common false positives.
    candidates = [match.group(1) for match in _TICKER_RE.finditer(text)]
    stop = {
        "USD",
        "US",
        "SEC",
        "ETF",
        "CEO",
        "CFTC",
        "EU",
        "UK",
    }
    assets: list[str] = []
    for token in candidates:
        if token in stop:
            continue
        if token.isalpha() and token == token.upper():
            assets.append(token)
    # de-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for a in assets:
        if a not in seen:
            ordered.append(a)
            seen.add(a)
    return ordered


def extract_entities(_: str) -> list[str]:
    # Placeholder: entity extraction is intentionally minimal for v1 skeleton.
    return []


def resolve_jurisdiction(text: str) -> Jurisdiction:
    t = text.lower()
    # Only explicit cues; otherwise GLOBAL.
    if any(k in t for k in [" sec ", " u.s.", " us ", " united states", " cftc", " nyse", " nasdaq"]):
        return Jurisdiction.US
    if any(k in t for k in [" eu ", " european union", " esma", " mica", " ecb"]):
        return Jurisdiction.EUROPE
    if any(k in t for k in [" uk ", " united kingdom", " fca "]):
        return Jurisdiction.EUROPE
    if any(k in t for k in [" canada", " osc ", " csa ", " mexico", " brazil", " argentina", " chile"]):
        return Jurisdiction.AMERICAS_NON_US
    if any(k in t for k in [" japan", " singapore", " hong kong", " korea", " india", " china"]):
        return Jurisdiction.ASIA
    if any(k in t for k in [" australia", " new zealand"]):
        return Jurisdiction.OCEANIA
    if any(k in t for k in [" nigeria", " kenya", " south africa"]):
        return Jurisdiction.AFRICA
    return Jurisdiction.GLOBAL


def infer_sentiment(text: str) -> Sentiment:
    t = text.lower()
    if any(k in t for k in ["hack", "exploit", "lawsuit", "charges", "indict", "ban", "depeg"]):
        return Sentiment.negative
    if any(k in t for k in ["approval", "approved", "inflows", "record", "surge", "partnership"]):
        return Sentiment.positive
    return Sentiment.neutral


def _candidates(text: str) -> list[CandidateEvent]:
    t = text.lower()
    candidates: list[CandidateEvent] = []

    def add(event_type: EventType, confidence: float, impact_score: float) -> None:
        candidates.append(CandidateEvent(event_type=event_type, confidence=confidence, impact_score=impact_score))

    if "hack" in t or "exploit" in t or "breach" in t:
        add(EventType.EXCHANGE_HACK, confidence=0.75, impact_score=0.9)

    if "sec" in t or "cftc" in t or "enforcement" in t or "charges" in t or "lawsuit" in t:
        add(EventType.ENFORCEMENT_ACTION, confidence=0.7, impact_score=0.85)

    if "depeg" in t or "lost its peg" in t or "trading below $1" in t:
        add(EventType.STABLECOIN_DEPEG, confidence=0.75, impact_score=0.8)

    if "etf" in t and ("approved" in t or "approval" in t):
        add(EventType.ETF_APPROVAL, confidence=0.75, impact_score=0.75)

    if "etf" in t and ("rejected" in t or "rejection" in t or "denied" in t):
        add(EventType.ETF_REJECTION, confidence=0.75, impact_score=0.7)

    if "etf" in t and ("filed" in t or "filing" in t or "s-1" in t or "19b-4" in t):
        add(EventType.ETF_FILING, confidence=0.7, impact_score=0.6)

    if "etf" in t and ("inflow" in t or "inflows" in t):
        add(EventType.ETF_INFLOW, confidence=0.7, impact_score=0.65)

    if "etf" in t and ("outflow" in t or "outflows" in t):
        add(EventType.ETF_OUTFLOW, confidence=0.7, impact_score=0.6)

    if "stablecoin" in t and ("mint" in t or "issued" in t or "issuance" in t):
        add(EventType.STABLECOIN_ISSUANCE, confidence=0.65, impact_score=0.55)

    if "exchange" in t and ("inflow" in t or "inflows" in t):
        add(EventType.CEX_INFLOW, confidence=0.6, impact_score=0.5)

    if "exchange" in t and ("outflow" in t or "outflows" in t):
        add(EventType.CEX_OUTFLOW, confidence=0.6, impact_score=0.5)

    if "upgrade" in t or "hard fork" in t or "mainnet" in t:
        add(EventType.PROTOCOL_UPGRADE, confidence=0.6, impact_score=0.55)

    if "miner" in t and ("shutdown" in t or "shut down" in t or "halt" in t):
        add(EventType.MINER_SHUTDOWN, confidence=0.6, impact_score=0.5)

    return candidates


def select_primary_event(text: str) -> CandidateEvent:
    candidates = _candidates(text)
    if not candidates:
        return CandidateEvent(event_type=EventType.UNKNOWN, confidence=0.4, impact_score=0.2)

    # Highest impact wins; then confidence; then precedence; then first-mention order.
    def key(c: CandidateEvent) -> tuple[float, float, int]:
        return (c.impact_score, c.confidence, -_PRECEDENCE.get(c.event_type, 999))

    # Sort descending by impact/confidence; precedence handled by negative rank above.
    best = max(candidates, key=key)
    return best
