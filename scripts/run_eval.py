from __future__ import annotations

import json
import os
from pathlib import Path

from crypto_news_parser.main import parse
from crypto_news_parser.golden import load_golden_cases
from crypto_news_parser.models import EventType, Jurisdiction, MarketDirection, ParseRequest, Sentiment, TimeHorizon


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "eval" / "golden_cases.jsonl"
    cases = load_golden_cases(path)
    strict = os.getenv("RUN_GOLDEN_STRICT") == "1"

    total = 0
    passed = 0

    for case in cases:
        case_id = case["id"]
        text = case["text"]
        expected = case.get("expected", {})

        # Call the endpoint function directly (no HTTP) for cheap local eval.
        result = parse.__wrapped__(
            ParseRequest(
                text=text,
                deterministic=True,
                source_url=case.get("source_url"),
                source_name=case.get("source_name"),
                source_published_at=case.get("source_published_at"),
            ),
            authorization=None,
        )  # type: ignore[attr-defined]
        # If it's async (FastAPI), __wrapped__ returns coroutine in some contexts.
        if hasattr(result, "__await__"):
            import asyncio

            result = asyncio.get_event_loop().run_until_complete(result)  # type: ignore[assignment]

        actual = result.model_dump()

        comparable_expected = dict(expected)

        # Prefer v1_* mappings when present (lets dataset keep richer labels).
        if "v1_event_type" in comparable_expected:
            comparable_expected["event_type"] = comparable_expected.pop("v1_event_type")
        if "v1_jurisdiction" in comparable_expected:
            comparable_expected["jurisdiction"] = comparable_expected.pop("v1_jurisdiction")
        if not strict:
            if (et := comparable_expected.get("event_type")) is not None and et not in {e.value for e in EventType}:
                comparable_expected.pop("event_type", None)
            if (j := comparable_expected.get("jurisdiction")) is not None and j not in {e.value for e in Jurisdiction}:
                comparable_expected.pop("jurisdiction", None)
            if (s := comparable_expected.get("sentiment")) is not None and s not in {e.value for e in Sentiment}:
                comparable_expected.pop("sentiment", None)
            if (md := comparable_expected.get("market_direction")) is not None and md not in {e.value for e in MarketDirection}:
                comparable_expected.pop("market_direction", None)
            if (th := comparable_expected.get("time_horizon")) is not None and th not in {e.value for e in TimeHorizon}:
                comparable_expected.pop("time_horizon", None)

        ok = True
        for k, v in comparable_expected.items():
            if actual.get(k) != v:
                ok = False

        total += 1
        if ok:
            passed += 1
            print(f"PASS {case_id}")
        else:
            print(f"FAIL {case_id}")
            print(" expected:", comparable_expected)
            print(" actual:", {k: actual.get(k) for k in comparable_expected.keys()})

    print(f"\n{passed}/{total} passed")


if __name__ == "__main__":
    main()
