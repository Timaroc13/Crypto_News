from __future__ import annotations

import json
from pathlib import Path

from crypto_news_parser.main import parse
from crypto_news_parser.models import ParseRequest


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "eval" / "golden_cases.jsonl"
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    total = 0
    passed = 0

    for line in lines:
        case = json.loads(line)
        case_id = case["id"]
        text = case["text"]
        expected = case.get("expected", {})

        # Call the endpoint function directly (no HTTP) for cheap local eval.
        result = parse.__wrapped__(ParseRequest(text=text, deterministic=True), authorization=None)  # type: ignore[attr-defined]
        # If it's async (FastAPI), __wrapped__ returns coroutine in some contexts.
        if hasattr(result, "__await__"):
            import asyncio

            result = asyncio.get_event_loop().run_until_complete(result)  # type: ignore[assignment]

        actual = result.model_dump()

        ok = True
        for k, v in expected.items():
            if actual.get(k) != v:
                ok = False

        total += 1
        if ok:
            passed += 1
            print(f"PASS {case_id}")
        else:
            print(f"FAIL {case_id}")
            print(" expected:", expected)
            print(" actual:", {k: actual.get(k) for k in expected.keys()})

    print(f"\n{passed}/{total} passed")


if __name__ == "__main__":
    main()
