import json
from pathlib import Path

from fastapi.testclient import TestClient

from crypto_news_parser.main import app


def test_golden_cases_match_expected_minimums() -> None:
    path = Path(__file__).resolve().parents[1] / "eval" / "golden_cases.jsonl"
    if not path.exists():
        return

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # Skip if user hasn't added cases yet (keep CI green on fresh scaffold).
    if len(lines) <= 1:
        return

    client = TestClient(app)

    for line in lines:
        case = json.loads(line)
        resp = client.post("/parse", json={"text": case["text"], "deterministic": True})
        assert resp.status_code == 200
        data = resp.json()

        expected = case.get("expected", {})
        assert expected.get("event_type") is not None, f"{case['id']} missing expected.event_type"

        for key, value in expected.items():
            assert data.get(key) == value, f"{case['id']} mismatch for {key}: expected {value}, got {data.get(key)}"
