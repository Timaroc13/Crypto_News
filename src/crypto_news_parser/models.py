from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

MAX_TEXT_LENGTH = 20_000


class EventType(str, Enum):
    # Primary taxonomy: user's MECE buckets + explicit fallbacks.
    UNKNOWN = "UNKNOWN"
    MISC_OTHER = "MISC_OTHER"

    # Regulation, Policy & Government
    REGULATORY_ACTION_ENFORCEMENT = "REGULATORY_ACTION_ENFORCEMENT"
    LEGISLATION_POLICY_DEVELOPMENT = "LEGISLATION_POLICY_DEVELOPMENT"
    GOVERNMENT_CENTRAL_BANK_INITIATIVES = "GOVERNMENT_CENTRAL_BANK_INITIATIVES"

    # Institutions, Markets & Capital
    INSTITUTIONAL_ADOPTION_STRATEGY = "INSTITUTIONAL_ADOPTION_STRATEGY"
    CAPITAL_MARKETS_ACTIVITY = "CAPITAL_MARKETS_ACTIVITY"
    FUNDING_INVESTMENT_MA = "FUNDING_INVESTMENT_MA"
    MARKET_STRUCTURE_LIQUIDITY_SHIFTS = "MARKET_STRUCTURE_LIQUIDITY_SHIFTS"

    # Companies & Organizations
    COMPANY_FINANCIAL_PERFORMANCE = "COMPANY_FINANCIAL_PERFORMANCE"
    CORPORATE_GOVERNANCE_LEADERSHIP_CHANGES = "CORPORATE_GOVERNANCE_LEADERSHIP_CHANGES"
    BUSINESS_MODEL_STRATEGIC_PIVOT = "BUSINESS_MODEL_STRATEGIC_PIVOT"

    # Protocols, Networks & Technology
    PROTOCOL_UPGRADES_NETWORK_CHANGES = "PROTOCOL_UPGRADES_NETWORK_CHANGES"
    NEW_PROTOCOL_PRODUCT_LAUNCHES = "NEW_PROTOCOL_PRODUCT_LAUNCHES"
    INTEROPERABILITY_INFRA_DEVELOPMENTS = "INTEROPERABILITY_INFRA_DEVELOPMENTS"
    SECURITY_INCIDENTS_EXPLOITS = "SECURITY_INCIDENTS_EXPLOITS"

    # Assets, Tokens & Economics
    TOKEN_ECONOMICS_SUPPLY_EVENTS = "TOKEN_ECONOMICS_SUPPLY_EVENTS"
    STABLECOINS_MONETARY_MECHANICS = "STABLECOINS_MONETARY_MECHANICS"
    YIELD_RATES_RETURN_DYNAMICS = "YIELD_RATES_RETURN_DYNAMICS"

    # Ecosystem & Use-Cases
    RWA_DEVELOPMENTS = "RWA_DEVELOPMENTS"
    PAYMENTS_COMMERCE_CONSUMER_ADOPTION = "PAYMENTS_COMMERCE_CONSUMER_ADOPTION"
    ECOSYSTEM_PARTNERSHIPS_INTEGRATIONS = "ECOSYSTEM_PARTNERSHIPS_INTEGRATIONS"


class EventTypeV1(str, Enum):
    """Legacy v1 taxonomy (kept for best-effort mapping)."""

    UNKNOWN = "UNKNOWN"

    ETF_APPROVAL = "ETF_APPROVAL"
    ETF_REJECTION = "ETF_REJECTION"
    ETF_FILING = "ETF_FILING"
    ETF_INFLOW = "ETF_INFLOW"
    ETF_OUTFLOW = "ETF_OUTFLOW"

    ENFORCEMENT_ACTION = "ENFORCEMENT_ACTION"
    EXCHANGE_HACK = "EXCHANGE_HACK"

    STABLECOIN_ISSUANCE = "STABLECOIN_ISSUANCE"
    STABLECOIN_DEPEG = "STABLECOIN_DEPEG"

    CEX_INFLOW = "CEX_INFLOW"
    CEX_OUTFLOW = "CEX_OUTFLOW"

    PROTOCOL_UPGRADE = "PROTOCOL_UPGRADE"
    MINER_SHUTDOWN = "MINER_SHUTDOWN"


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class MarketDirection(str, Enum):
    bullish = "bullish"
    bearish = "bearish"
    neutral = "neutral"


class TimeHorizon(str, Enum):
    short_term = "short_term"
    medium_term = "medium_term"
    long_term = "long_term"


class Jurisdiction(str, Enum):
    US = "US"
    AMERICAS_NON_US = "AMERICAS_NON_US"
    EUROPE = "EUROPE"
    ASIA = "ASIA"
    AFRICA = "AFRICA"
    OCEANIA = "OCEANIA"
    GLOBAL = "GLOBAL"


class JurisdictionBasis(str, Enum):
    explicit = "explicit"
    implied = "implied"
    none = "none"


class ParseRequest(BaseModel):
    text: str = Field(..., description="Crypto-related text to parse")
    deterministic: bool = Field(False, description="If true, output is reproducible")

    # Optional caller-provided id to correlate parses and feedback.
    input_id: str | None = Field(
        None,
        description="Optional caller-provided identifier for correlating parses and feedback",
    )

    # Optional metadata (v1): accepted for traceability; MUST NOT trigger any fetching.
    source_url: str | None = Field(None, description="Optional source URL (not fetched)")
    source_name: str | None = Field(None, description="Optional source name/publisher")
    source_published_at: str | None = Field(
        None,
        description="Optional published timestamp as ISO 8601 string (not interpreted in v1)",
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if value is None:
            raise ValueError("text is required")
        value = value.strip()
        if not value:
            raise ValueError("text must be non-empty")
        return value

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if any(ch.isspace() for ch in value):
            raise ValueError("source_url must not contain whitespace")
        # Keep validation lightweight; accept absolute URLs/URIs (no fetching is performed).
        # This supports schemes like https://, http://, synthetic://, ipfs://, etc.
        if "://" not in value and not value.startswith("urn:"):
            raise ValueError("source_url must be an absolute URL/URI (e.g., https://...)")
        if len(value) > 2048:
            raise ValueError("source_url is too long")
        return value


class ParseUrlRequest(BaseModel):
    url: str = Field(..., description="Absolute http(s) URL to fetch and parse")
    deterministic: bool = Field(False, description="If true, output is reproducible given fetched content")

    # Optional caller-provided id to correlate parses and feedback.
    input_id: str | None = Field(
        None,
        description="Optional caller-provided identifier for correlating parses and feedback",
    )

    # Optional metadata (traceability only).
    source_name: str | None = Field(None, description="Optional source name/publisher")
    source_published_at: str | None = Field(
        None,
        description="Optional published timestamp as ISO 8601 string (not interpreted in v1)",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if value is None:
            raise ValueError("url is required")
        value = value.strip()
        if not value:
            raise ValueError("url must be non-empty")
        if any(ch.isspace() for ch in value):
            raise ValueError("url must not contain whitespace")
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("url must start with http:// or https://")
        if len(value) > 2048:
            raise ValueError("url is too long")
        return value


class FeedbackRequest(BaseModel):
    parse_id: int | None = Field(
        default=None,
        description="Optional parse id returned in X-Parse-Id header when persistence is enabled",
    )
    input_id: str | None = Field(
        default=None,
        description="Optional caller-provided id to correlate feedback when parse_id is not available",
    )
    text: str | None = Field(
        default=None,
        description="Optional raw text (required for export when parse_id is not provided)",
    )
    expected: dict[str, Any] = Field(
        default_factory=dict,
        description="Corrected fields (e.g., event_type, event_subtype, jurisdiction, assets, entities)",
    )
    notes: str | None = Field(default=None, description="Optional free-form notes")

    @field_validator("expected")
    @classmethod
    def validate_expected(cls, value: dict[str, Any]) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("expected must be an object")
        return value


class FeedbackResponse(BaseModel):
    feedback_id: int
    status: str = "stored"


class ParseResponse(BaseModel):
    event_type: EventType
    v1_event_type: EventTypeV1 | None = Field(
        default=None,
        description="Optional best-effort mapping to the legacy v1 event_type taxonomy",
    )
    event_subtype: str | None = Field(
        default=None,
        description="Optional finer-grained label consistent with event_type",
    )
    topics: list[str]
    assets: list[str]
    entities: list[str]
    jurisdiction: Jurisdiction
    jurisdiction_basis: JurisdictionBasis | None = Field(
        default=None,
        description='Optional explanation of how jurisdiction was determined: "explicit" | "implied" | "none".',
    )
    jurisdiction_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score for jurisdiction inference.",
    )
    sentiment: Sentiment
    impact_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)

    market_direction: MarketDirection | None = None
    systemic_risk: bool | None = None
    retail_relevant: bool | None = None
    time_horizon: TimeHorizon | None = None

    schema_version: str
    model_version: str


class ErrorEnvelope(BaseModel):
    error: ErrorObject


class ErrorObject(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
