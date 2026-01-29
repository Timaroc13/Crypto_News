from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

MAX_TEXT_LENGTH = 20_000


class EventType(str, Enum):
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


class ParseRequest(BaseModel):
    text: str = Field(..., description="Crypto-related text to parse")
    deterministic: bool = Field(False, description="If true, output is reproducible")

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
        # Keep validation lightweight; we only accept http(s) to avoid ambiguity.
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("source_url must start with http:// or https://")
        if len(value) > 2048:
            raise ValueError("source_url is too long")
        return value


class ParseResponse(BaseModel):
    event_type: EventType
    topics: list[str]
    assets: list[str]
    entities: list[str]
    jurisdiction: Jurisdiction
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
