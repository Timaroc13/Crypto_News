from __future__ import annotations

from fastapi.testclient import TestClient

import crypto_news_parser.main as main_mod
from crypto_news_parser.llm_adapter import PROMPT_VERSION, LLMRefinement
from crypto_news_parser.models import EventType


def test_llm_refinement_applies_on_low_confidence(monkeypatch) -> None:
    client = TestClient(main_mod.app)

    class FakeProvider:
        name = "fake"
        supports_determinism = True

        def __init__(self) -> None:
            self.last_prompt_version: str | None = None

        async def refine(self, request):
            self.last_prompt_version = request.prompt_version
            return LLMRefinement(
                event_type=EventType.REGULATORY_GUIDANCE,
                assets=["BTC"],
                entities=["BlackRock"],
            )

    provider = FakeProvider()
    monkeypatch.setattr(main_mod, "get_llm_provider", lambda: provider)

    resp = client.post("/parse", json={"text": "I ate breakfast and went for a walk."})
    assert resp.status_code == 200
    data = resp.json()

    assert data["event_type"] == "REGULATORY_GUIDANCE"
    assert "BTC" in data["assets"]
    assert "BlackRock" in data["entities"]
    assert provider.last_prompt_version == PROMPT_VERSION


def test_llm_refinement_skips_when_deterministic_not_supported(monkeypatch) -> None:
    client = TestClient(main_mod.app)

    class NonDeterministicProvider:
        name = "non_det"
        supports_determinism = False

        async def refine(self, request):
            raise AssertionError("refine() should not be called")

    monkeypatch.setattr(main_mod, "get_llm_provider", lambda: NonDeterministicProvider())

    resp = client.post(
        "/parse",
        json={"text": "I ate breakfast and went for a walk.", "deterministic": True},
    )
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "UNKNOWN"
