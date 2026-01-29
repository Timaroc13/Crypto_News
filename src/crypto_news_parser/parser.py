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


_ASSET_ALLOWLIST = {
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "BNB",
    "ADA",
    "DOGE",
    "LTC",
    "AVAX",
    "DOT",
    "LINK",
    "UNI",
    "AAVE",
    "USDT",
    "USDC",
}


_ASSET_NAME_PATTERNS: list[tuple[str, str]] = [
    (r"\bbitcoin(?:'s|’s)?\b", "BTC"),
    (r"\bethereum(?:'s|’s)?\b", "ETH"),
    (r"\bether(?:'s|’s)?\b", "ETH"),
    (r"\bsolana(?:'s|’s)?\b", "SOL"),
    (r"\btether(?:'s|’s)?\b", "USDT"),
    (r"\busdc\b", "USDC"),
]


_ENTITY_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9'’\-\.]*")


_ENTITY_SINGLE_WORD_ALLOW = {
    # Common entities from the current golden set / crypto news.
    "Bybit",
    "Ledger",
    "Robinhood",
    "BlackRock",
    "CoinDesk",
    "Cointelegraph",
    "Reuters",
}


_ENTITY_SINGLE_WORD_DENY = {
    # Generic sentence starters and common nouns.
    "A",
    "An",
    "The",
    "This",
    "That",
    "These",
    "Those",
    "Crypto",
    "Trading",
    "Tokenized",
    "Digital",
    "New",
    "York",
    "White",
    "House",
}


_ENTITY_ALLCAPS_DENY = {
    # Avoid duplicating assets/jurisdiction/regulators as entities.
    "USD",
    "US",
    "UAE",
    "EU",
    "UK",
    "SEC",
    "CFTC",
    "DOJ",
    "ETF",
    "IBAN",
}


_ENTITY_CONNECTORS = {"of", "the", "and", "for"}


def _clean_entity_token(token: str) -> str:
    t = token.strip("\"'“”‘’.,;:()[]{}")
    # Normalize possessives like “Saylor’s” -> “Saylor”.
    if t.endswith("'s") or t.endswith("’s"):
        t = t[:-2]
    return t


def _is_title_token(token: str) -> bool:
    if not token:
        return False
    if not token[0].isupper():
        return False
    # Require at least one lowercase to avoid treating tickers as Title Case.
    return any(c.islower() for c in token[1:])


def _is_allcaps_token(token: str) -> bool:
    if not token:
        return False
    return token.isupper() and any(c.isalpha() for c in token) and len(token) >= 2


def extract_assets(text: str) -> list[str]:
    # Best-effort: favor precision over recall.
    # 1) Map common asset names to tickers.
    t = text.lower()
    assets: list[str] = []
    for pattern, ticker in _ASSET_NAME_PATTERNS:
        if re.search(pattern, t):
            assets.append(ticker)

    # 2) Capture explicit tickers (e.g., BTC, $BTC) but only from an allowlist.
    for match in _TICKER_RE.finditer(text):
        token = match.group(1)
        if token in _ASSET_ALLOWLIST:
            assets.append(token)
    # de-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for a in assets:
        if a not in seen:
            ordered.append(a)
            seen.add(a)
    return ordered


def extract_entities(text: str) -> list[str]:
    # Conservative heuristic: extract sequences of capitalized tokens.
    tokens: list[str] = []
    for m in _ENTITY_TOKEN_RE.finditer(text):
        cleaned = _clean_entity_token(m.group(0))
        if cleaned:
            tokens.append(cleaned)

    entities: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        next_tok = tokens[i + 1] if i + 1 < len(tokens) else ""

        starts = _is_title_token(tok) or (
            _is_allcaps_token(tok) and tok not in _ENTITY_ALLCAPS_DENY and _is_title_token(next_tok)
        )
        if not starts:
            i += 1
            continue

        phrase_tokens: list[str] = [tok]
        i += 1

        while i < len(tokens):
            t = tokens[i]
            if (
                t.lower() in _ENTITY_CONNECTORS
                and i + 1 < len(tokens)
                and _is_title_token(tokens[i + 1])
            ):
                phrase_tokens.append(t)
                i += 1
                continue
            if _is_title_token(t):
                phrase_tokens.append(t)
                i += 1
                continue
            break

        phrase = " ".join(phrase_tokens).strip()
        if not phrase:
            continue

        # Filter very short or generic results.
        if " " not in phrase:
            if phrase in _ENTITY_SINGLE_WORD_DENY:
                continue
            if phrase not in _ENTITY_SINGLE_WORD_ALLOW:
                # Avoid picking up random single capitalized words.
                continue

        entities.append(phrase)

    # de-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for e in entities:
        if e not in seen:
            ordered.append(e)
            seen.add(e)
    return ordered


def resolve_jurisdiction(text: str) -> Jurisdiction:
    t = text.lower()

    def has_any(*patterns: str) -> bool:
        return any(re.search(p, t) for p in patterns)

    # Only explicit cues; otherwise GLOBAL.
    if has_any(
        r"\bunited states\b",
        r"\bu\.?s\.?\b",
        r"\bsec\b",
        r"\bcftc\b",
        r"\bdoj\b",
        r"\bnyse\b",
        r"\bnasdaq\b",
    ):
        return Jurisdiction.US

    if has_any(
        r"\beuropean union\b",
        r"\beu\b",
        r"\besma\b",
        r"\bmica\b",
        r"\becb\b",
        r"\bunited kingdom\b",
        r"\buk\b",
        r"\bfca\b",
        r"\brussia\b",
        r"\brussian\b",
        r"\bmoscow\b",
    ):
        return Jurisdiction.EUROPE

    if has_any(
        r"\bcanada\b",
        r"\bmexico\b",
        r"\bbrazil\b",
        r"\bargentina\b",
        r"\bchile\b",
        r"\bosc\b",
        r"\bcsa\b",
    ):
        return Jurisdiction.AMERICAS_NON_US

    if has_any(
        r"\bjapan\b",
        r"\bsingapore\b",
        r"\bhong\s+kong\b",
        r"\b(korea|south korea|north korea)\b",
        r"\bindia\b",
        r"\bchina\b",
        r"\buae\b",
        r"\bunited arab emirates\b",
        r"\bdubai\b",
        r"\babu dhabi\b",
    ):
        return Jurisdiction.ASIA

    if has_any(r"\baustralia\b", r"\bnew zealand\b"):
        return Jurisdiction.OCEANIA

    if has_any(r"\bnigeria\b", r"\bkenya\b", r"\bsouth africa\b"):
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
        candidates.append(
            CandidateEvent(
                event_type=event_type,
                confidence=confidence,
                impact_score=impact_score,
            )
        )

    if "hack" in t or "exploit" in t or "breach" in t:
        add(EventType.EXCHANGE_HACK, confidence=0.75, impact_score=0.9)

    regulators = [
        "sec",
        "cftc",
        "doj",
        "finra",
        "fca",
        "esma",
        "ofac",
    ]
    enforcement_words = [
        "enforcement",
        "charges",
        "charged",
        "lawsuit",
        "sues",
        "sued",
        "settlement",
        "fine",
        "penalty",
        "indict",
        "indicted",
        "arrest",
        "probe",
        "investigation",
    ]
    if any(w in t for w in enforcement_words) and any(r in t for r in regulators):
        add(EventType.ENFORCEMENT_ACTION, confidence=0.72, impact_score=0.85)

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

    if "stablecoin" in t and any(
        w in t
        for w in [
            "mint",
            "issued",
            "issuance",
            "launch",
            "launched",
            "launches",
            "registered",
            "backed",
            "pegged",
            "introduced",
        ]
    ):
        add(EventType.STABLECOIN_ISSUANCE, confidence=0.68, impact_score=0.55)

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
