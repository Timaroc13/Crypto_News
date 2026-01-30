from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import crypto_news_parser.main as main_mod
from crypto_news_parser.storage import export_feedback_cases


@pytest.fixture()
def client(tmp_path: Path, monkeypatch) -> TestClient:
    db = tmp_path / "test.sqlite3"
    monkeypatch.setenv("ENABLE_PERSISTENCE", "1")
    monkeypatch.setenv("DB_PATH", str(db))
    return TestClient(main_mod.app)


def test_parse_persists_and_sets_header(client: TestClient) -> None:
    resp = client.post(
        "/parse",
        json={"text": "The U.S. SEC clarified rules for tokenized stocks.", "input_id": "x1"},
    )
    assert resp.status_code == 200
    assert "X-Parse-Id" in resp.headers
    assert int(resp.headers["X-Parse-Id"]) > 0


def test_feedback_with_parse_id_and_export(client: TestClient) -> None:
    parse_resp = client.post(
        "/parse",
        json={"text": "The U.S. SEC clarified rules for tokenized stocks.", "input_id": "x2"},
    )
    assert parse_resp.status_code == 200
    parse_id = int(parse_resp.headers["X-Parse-Id"])

    fb_resp = client.post(
        "/feedback",
        json={
            "parse_id": parse_id,
            "expected": {"event_type": "LEGISLATION_POLICY_DEVELOPMENT", "jurisdiction": "US"},
            "notes": "looks right",
        },
    )
    assert fb_resp.status_code == 200
    body = fb_resp.json()
    assert body["status"] == "stored"
    assert int(body["feedback_id"]) > 0

    cases = export_feedback_cases()
    assert len(cases) == 1
    obj = cases[0]
    assert obj["id"].startswith("feedback-")
    assert isinstance(obj["text"], str) and obj["text"]
    assert obj["expected"]["event_type"] == "LEGISLATION_POLICY_DEVELOPMENT"


def test_feedback_disabled_returns_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_PERSISTENCE", raising=False)
    monkeypatch.setenv("DB_PATH", str(tmp_path / "nope.sqlite3"))
    client = TestClient(main_mod.app)
    resp = client.post("/feedback", json={"input_id": "x3", "expected": {"event_type": "UNKNOWN"}})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PERSISTENCE_DISABLED"
