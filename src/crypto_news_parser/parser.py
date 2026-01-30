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
    # Lower number = higher precedence (used only for tie-breaks).
    EventType.CRYPTO_REGULATION_RESTRICTION: 1,
    EventType.REGULATORY_GUIDANCE: 2,
    EventType.STABLECOIN_LAUNCH: 3,
    EventType.STABLECOIN_RESERVE_UPDATE: 3,
    EventType.STABLECOIN_IMPACT_WARNING: 4,
    EventType.FUND_RAISE: 5,
    EventType.STRATEGIC_INVESTMENT: 5,
    EventType.CORPORATE_BITCOIN_PURCHASE: 5,
    EventType.IPO_FILING: 6,
    EventType.IPO_MARKET_DEBUT: 6,
    EventType.IPO_PLANNING: 6,
    EventType.TOKENIZED_ASSET_VOLUME_SURGE: 7,
    EventType.TOKENIZED_EQUITIES_STRATEGY: 7,
    EventType.CRYPTO_EXCHANGE_PRODUCT_EXPANSION: 8,
    EventType.CRYPTO_PAYMENTS_COMPANY_UPDATE: 8,
    EventType.NETWORK_VALIDATOR_DECLINE: 9,
    EventType.CRYPTO_MARKET_VOLATILITY: 10,
    EventType.MACRO_MARKET_SHOCK: 10,
    EventType.CRYPTO_POLICY_MEETING: 11,
    EventType.MISC_OTHER: 98,
    EventType.UNKNOWN: 99,
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


def _is_crypto_related(text: str) -> bool:
    t = text.lower()
    crypto_cues = [
        "crypto",
        "cryptocurrency",
        "blockchain",
        "bitcoin",
        "ethereum",
        "stablecoin",
        "token",
        "defi",
        "exchange",
        "wallet",
        "web3",
        "onchain",
    ]
    if any(cue in t for cue in crypto_cues):
        return True
    # If we extracted a known asset ticker, treat as crypto-related.
    if any(ticker in extract_assets(text) for ticker in _ASSET_ALLOWLIST):
        return True
    return False


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


def infer_event_subtype(text: str, event_type: EventType) -> str | None:
    """Best-effort optional subtype, consistent with the selected event_type.

    This intentionally favors precision over recall.
    """

    t = text.lower()

    if event_type == EventType.CRYPTO_REGULATION_RESTRICTION:
        if any(w in t for w in ["lawsuit", "sues", "sued", "sue "]):
            return "regulation.enforcement.lawsuit"
        if any(w in t for w in ["fine", "penalty", "fined", "civil penalty"]):
            return "regulation.enforcement.fine"
        if any(w in t for w in ["settlement", "settled"]):
            return "regulation.enforcement.settlement"
        if any(w in t for w in ["ban", "banned", "prohibit", "prohibited", "restriction"]):
            return "regulation.restriction"
        return None

    if event_type == EventType.REGULATORY_GUIDANCE:
        if any(w in t for w in ["bill", "draft bill", "policy", "framework", "consultation"]):
            return "regulation.policy"
        if any(w in t for w in ["guidance", "clarified", "clarifies", "rules"]):
            return "regulation.guidance"
        return None

    if event_type == EventType.CRYPTO_POLICY_MEETING:
        return "regulation.policy.meeting"

    if event_type == EventType.STABLECOIN_LAUNCH:
        if "registered" in t or "registration" in t:
            return "stablecoin.launch.registered"
        return "stablecoin.launch"

    if event_type == EventType.STABLECOIN_RESERVE_UPDATE:
        return "stablecoin.reserves.update"

    if event_type == EventType.STABLECOIN_IMPACT_WARNING:
        return "stablecoin.risk.warning"

    if event_type == EventType.FUND_RAISE:
        return "institutions.funding"

    if event_type == EventType.STRATEGIC_INVESTMENT:
        return "institutions.investment"

    if event_type == EventType.CORPORATE_BITCOIN_PURCHASE:
        return "institutions.treasury.btc_purchase"

    if event_type == EventType.CRYPTO_MARKET_VOLATILITY:
        return "markets.volatility"

    if event_type == EventType.MACRO_MARKET_SHOCK:
        return "macro.shock"

    if event_type == EventType.NETWORK_VALIDATOR_DECLINE:
        return "network.validators.decline"

    if event_type == EventType.CRYPTO_EXCHANGE_PRODUCT_EXPANSION:
        return "market_structure.exchange.product_expansion"

    if event_type == EventType.CRYPTO_PAYMENTS_COMPANY_UPDATE:
        return "payments.company.update"

    if event_type == EventType.TOKENIZED_ASSET_VOLUME_SURGE:
        return "tokenization.asset.volume_surge"

    if event_type == EventType.TOKENIZED_EQUITIES_STRATEGY:
        return "tokenization.equities.strategy"

    if event_type == EventType.IPO_FILING:
        return "capital_markets.ipo.filing"

    if event_type == EventType.IPO_PLANNING:
        return "capital_markets.ipo.planning"

    if event_type == EventType.IPO_MARKET_DEBUT:
        return "capital_markets.ipo.market_debut"

    if event_type == EventType.MISC_OTHER:
        # Preserve some high-signal subtypes for common crypto narratives.
        if any(w in t for w in ["hack", "exploit", "breach"]):
            if "breach" in t:
                return "security.exchange_hack.breach"
            if "exploit" in t:
                return "security.exchange_hack.exploit"
            return "security.exchange_hack.hack"
        if "hard fork" in t:
            return "protocol.upgrade.hard_fork"
        if "mainnet" in t and "upgrade" in t:
            return "protocol.upgrade.mainnet"
        if "upgrade" in t:
            return "protocol.upgrade.upgrade"
        if "miner" in t and any(w in t for w in ["shutdown", "shut down", "halt"]):
            if "halt" in t:
                return "protocol.mining.halt"
            return "protocol.mining.shutdown"
        return "misc"

    if event_type == EventType.UNKNOWN:
        return None

    return None


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

    regulators = ["sec", "cftc", "doj", "finra", "fca", "esma", "ofac", "regulator"]

    # Regulation / restrictions (includes enforcement-like language).
    restriction_words = [
        "lawsuit",
        "sues",
        "sued",
        "charges",
        "charged",
        "indict",
        "indicted",
        "ban",
        "banned",
        "prohibit",
        "prohibited",
        "restriction",
        "restricted",
        "crackdown",
    ]
    if any(w in t for w in restriction_words) and any(r in t for r in regulators):
        add(EventType.CRYPTO_REGULATION_RESTRICTION, confidence=0.72, impact_score=0.85)

    guidance_words = [
        "guidance",
        "clarified",
        "clarifies",
        "rules",
        "framework",
        "consultation",
        "bill",
        "draft bill",
        "policy",
    ]
    if any(w in t for w in guidance_words) and (_is_crypto_related(text) or any(r in t for r in regulators)):
        add(EventType.REGULATORY_GUIDANCE, confidence=0.66, impact_score=0.65)

    if any(w in t for w in ["meeting", "summit", "hearing", "roundtable"]) and any(
        r in t for r in regulators
    ):
        add(EventType.CRYPTO_POLICY_MEETING, confidence=0.62, impact_score=0.55)

    # Stablecoins
    if "stablecoin" in t and any(w in t for w in ["launch", "launched", "launches", "introduced"]):
        add(EventType.STABLECOIN_LAUNCH, confidence=0.7, impact_score=0.7)
    if "stablecoin" in t and any(w in t for w in ["reserve", "reserves", "attestation", "audit"]):
        add(EventType.STABLECOIN_RESERVE_UPDATE, confidence=0.68, impact_score=0.65)
    if "stablecoin" in t and any(w in t for w in ["warning", "warned", "risk", "threat", "impact"]):
        add(EventType.STABLECOIN_IMPACT_WARNING, confidence=0.6, impact_score=0.55)

    # Institutions / funding
    if any(
        w in t
        for w in [
            "series a",
            "series b",
            "series c",
            "funding round",
            "raised",
            "raise",
            "seed round",
            "venture",
        ]
    ):
        add(EventType.FUND_RAISE, confidence=0.65, impact_score=0.6)

    if any(w in t for w in ["strategic investment", "invested", "investment", "took a stake", "stake"]):
        add(EventType.STRATEGIC_INVESTMENT, confidence=0.6, impact_score=0.55)

    if ("bitcoin" in t or "btc" in t) and any(
        w in t for w in ["purchased", "purchase", "buys", "bought", "acquired", "added"]
    ) and any(w in t for w in ["company", "firm", "treasury", "strategy"]):
        add(EventType.CORPORATE_BITCOIN_PURCHASE, confidence=0.66, impact_score=0.6)

    # Markets
    if _is_crypto_related(text) and any(
        w in t
        for w in [
            "volatility",
            "sell-off",
            "selloff",
            "plunge",
            "dump",
            "rally",
            "surge",
            "crash",
        ]
    ):
        add(EventType.CRYPTO_MARKET_VOLATILITY, confidence=0.58, impact_score=0.55)

    if any(w in t for w in ["fed", "interest rate", "inflation", "recession", "jobs report"]):
        add(EventType.MACRO_MARKET_SHOCK, confidence=0.55, impact_score=0.5)

    # Network health
    if any(w in t for w in ["validator", "validators"]) and any(
        w in t for w in ["decline", "dropped", "fallen", "drop", "down"]
    ):
        add(EventType.NETWORK_VALIDATOR_DECLINE, confidence=0.65, impact_score=0.55)

    # Exchanges / payments
    if "exchange" in t and any(
        w in t for w in ["launched", "launches", "roll out", "rolled out", "product", "derivatives", "options"]
    ):
        add(EventType.CRYPTO_EXCHANGE_PRODUCT_EXPANSION, confidence=0.6, impact_score=0.5)

    if any(w in t for w in ["payments", "payment", "settlement"]) and _is_crypto_related(text):
        add(EventType.CRYPTO_PAYMENTS_COMPANY_UPDATE, confidence=0.58, impact_score=0.45)

    # Tokenization
    if "tokenized" in t and any(w in t for w in ["volume", "volumes", "trading volume", "surged", "surge"]):
        add(EventType.TOKENIZED_ASSET_VOLUME_SURGE, confidence=0.65, impact_score=0.55)

    if "tokenized" in t and any(w in t for w in ["stock", "stocks", "equity", "equities"]):
        add(EventType.TOKENIZED_EQUITIES_STRATEGY, confidence=0.65, impact_score=0.55)

    # IPOs
    if "ipo" in t and any(w in t for w in ["filed", "filing", "f-1", "s-1"]):
        add(EventType.IPO_FILING, confidence=0.7, impact_score=0.6)
    if "ipo" in t and any(w in t for w in ["plans", "planning", "considering", "exploring"]):
        add(EventType.IPO_PLANNING, confidence=0.62, impact_score=0.5)
    if "ipo" in t and any(w in t for w in ["debut", "began trading", "priced", "listed"]):
        add(EventType.IPO_MARKET_DEBUT, confidence=0.68, impact_score=0.55)

    return candidates


def select_primary_event(text: str) -> CandidateEvent:
    candidates = _candidates(text)
    if not candidates:
        if _is_crypto_related(text):
            return CandidateEvent(event_type=EventType.MISC_OTHER, confidence=0.45, impact_score=0.25)
        return CandidateEvent(event_type=EventType.UNKNOWN, confidence=0.4, impact_score=0.2)

    # Highest impact wins; then confidence; then precedence; then first-mention order.
    def key(c: CandidateEvent) -> tuple[float, float, int]:
        return (c.impact_score, c.confidence, -_PRECEDENCE.get(c.event_type, 999))

    # Sort descending by impact/confidence; precedence handled by negative rank above.
    best = max(candidates, key=key)
    return best
