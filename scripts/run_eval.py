from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from crypto_news_parser.golden import load_golden_cases
from crypto_news_parser.main import app
from crypto_news_parser.models import (
    EventType,
    Jurisdiction,
    MarketDirection,
    Sentiment,
    TimeHorizon,
)


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "eval" / "golden_cases.jsonl"
    cases = load_golden_cases(path)

    synth_path = Path(__file__).resolve().parents[1] / "eval" / "synthetic_cases.jsonl"
    if synth_path.exists():
        cases.extend(load_golden_cases(synth_path))
    strict = os.getenv("RUN_GOLDEN_STRICT") == "1"

    client = TestClient(app)

    total = 0
    passed = 0

    for case in cases:
        case_id = case["id"]
        text = case["text"]
        expected = case.get("expected", {})

        resp = client.post(
            "/parse",
            json={
                "text": text,
                "deterministic": True,
                "source_url": case.get("source_url"),
                "source_name": case.get("source_name"),
                "source_published_at": case.get("source_published_at"),
            },
        )
        if resp.status_code != 200:
            print(f"FAIL {case_id}")
            print(" status:", resp.status_code)
            print(" body:", resp.text)
            total += 1
            continue

        actual = resp.json()

        comparable_expected = dict(expected)

        # Prefer v1_* mappings when present (lets dataset keep richer labels).
        if "v1_jurisdiction" in comparable_expected:
            comparable_expected["jurisdiction"] = comparable_expected.pop("v1_jurisdiction")
        if not strict:
            if (et := comparable_expected.get("event_type")) is not None and et not in {
                e.value for e in EventType
            }:
                comparable_expected.pop("event_type", None)
            if (j := comparable_expected.get("jurisdiction")) is not None and j not in {
                e.value for e in Jurisdiction
            }:
                comparable_expected.pop("jurisdiction", None)
            if (s := comparable_expected.get("sentiment")) is not None and s not in {
                e.value for e in Sentiment
            }:
                comparable_expected.pop("sentiment", None)
            if (md := comparable_expected.get("market_direction")) is not None and md not in {
                e.value for e in MarketDirection
            }:
                comparable_expected.pop("market_direction", None)
            if (th := comparable_expected.get("time_horizon")) is not None and th not in {
                e.value for e in TimeHorizon
            }:
                comparable_expected.pop("time_horizon", None)

        if not strict:
            # Non-strict is intended for iterative dataset building.
            # Only enforce "safe" expectations that don't depend on taxonomy maturity.
            comparable_expected = {
                k: comparable_expected[k]
                for k in ("assets", "entities")
                if k in comparable_expected
            }

        ok = True
        for k, v in comparable_expected.items():
            if k in {"assets", "entities"} and isinstance(v, list):
                actual_list = actual.get(k) or []
                if not isinstance(actual_list, list):
                    ok = False
                    continue
                # Treat expected lists as a subset requirement (actual can be richer).
                if not set(v).issubset(set(actual_list)):
                    ok = False
                    continue
            else:
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
