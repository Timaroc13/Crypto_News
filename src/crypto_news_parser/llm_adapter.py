from __future__ import annotations

import os
import zlib
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, field_validator

from .models import EventType

PROMPT_VERSION = "refine-v1-2026-01-29"


@dataclass(frozen=True)
class RefinementRequest:
    text: str
    heuristic_event_type: EventType
    heuristic_confidence: float
    heuristic_assets: tuple[str, ...]
    heuristic_entities: tuple[str, ...]
    prompt_version: str = PROMPT_VERSION
    deterministic: bool = False
    seed: int | None = None


class LLMRefinement(BaseModel):
    event_type: EventType | None = None
    assets: list[str] | None = None
    entities: list[str] | None = None

    @field_validator("assets", "entities")
    @classmethod
    def _normalize_list(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            s = item.strip()
            if s:
                cleaned.append(s)
        return cleaned


class LLMProvider(Protocol):
    name: str
    supports_determinism: bool

    async def refine(self, request: RefinementRequest) -> LLMRefinement:  # pragma: no cover
        ...


class NoopLLMProvider:
    name = "none"
    supports_determinism = True

    async def refine(self, request: RefinementRequest) -> LLMRefinement:
        _ = request
        return LLMRefinement()


def stable_seed(text: str, prompt_version: str = PROMPT_VERSION) -> int:
    """Deterministic seed derived from input text + prompt version."""

    payload = f"{prompt_version}\n{text}".encode("utf-8", errors="ignore")
    return int(zlib.crc32(payload) & 0xFFFFFFFF)


def get_provider_from_env() -> LLMProvider | None:
    """Returns an LLM provider if configured.

    By default, no provider is enabled and no network calls are made.
    """

    enabled = os.getenv("LLM_ENABLE", "").strip().lower() in {"1", "true", "yes"}
    if not enabled:
        return None

    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider in {"", "none"}:
        return None

    # Intentionally do not ship any network provider in v1.
    # This is a hook point for adding providers later.
    return None
