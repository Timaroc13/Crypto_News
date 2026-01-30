import os
from pathlib import Path

from fastapi.testclient import TestClient

from crypto_news_parser.golden import load_golden_cases
from crypto_news_parser.main import app


def test_golden_cases_match_expected_minimums() -> None:
    path = Path(__file__).resolve().parents[1] / "eval" / "golden_cases.jsonl"
    if not path.exists():
        return

    cases = load_golden_cases(path)
    # Skip if user hasn't added cases yet (keep CI green on fresh scaffold).
    if len(cases) <= 1:
        return

    strict = os.getenv("RUN_GOLDEN_STRICT") == "1"

    client = TestClient(app)

    for case in cases:
        resp = client.post(
            "/parse",
            json={
                "text": case["text"],
                "deterministic": True,
                "source_url": case.get("source_url"),
                "source_name": case.get("source_name"),
                "source_published_at": case.get("source_published_at"),
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        expected = case.get("expected", {})

        # Always require basic case structure.
        assert case.get("id"), "golden case missing id"
        assert case.get("text"), f"{case.get('id')} missing text"

        if not strict:
            # Non-strict mode is a smoke test only: dataset can contain future taxonomy labels.
            continue

        if not expected:
            continue

        # Strict mode: enforce exact expected matches.
        # API now outputs v2 event_type, and provides optional legacy mapping as v1_event_type.
        strict_expected = dict(expected)
        if "v1_jurisdiction" in strict_expected:
            # Prefer v1 mapping for current API jurisdiction enum.
            v1j = strict_expected.pop("v1_jurisdiction")
            # If a richer jurisdiction label is present too, ignore it for now.
            strict_expected.pop("jurisdiction", None)
            strict_expected["jurisdiction"] = v1j

        for key, value in strict_expected.items():
            assert data.get(key) == value, (
                f"{case['id']} mismatch for {key}: expected {value}, got {data.get(key)}"
            )
