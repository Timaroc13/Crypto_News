from fastapi.testclient import TestClient

from crypto_news_parser.main import app


client = TestClient(app)


def test_parse_returns_schema_fields() -> None:
    resp = client.post("/parse", json={"text": "BlackRock’s Bitcoin ETF saw $400M in inflows after SEC approval."})
    assert resp.status_code == 200
    data = resp.json()

    assert "event_type" in data
    assert "schema_version" in data
    assert "model_version" in data
    assert 0.0 <= data["impact_score"] <= 1.0
    assert 0.0 <= data["confidence"] <= 1.0


def test_parse_no_match_returns_unknown() -> None:
    resp = client.post("/parse", json={"text": "I ate breakfast and went for a walk."})
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "UNKNOWN"


def test_parse_rejects_empty_text() -> None:
    resp = client.post("/parse", json={"text": "   "})
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body


def test_parse_rejects_too_large() -> None:
    resp = client.post("/parse", json={"text": "x" * 20001})
    assert resp.status_code in {413, 422}


def test_stablecoin_launch_maps_to_issuance() -> None:
    text = (
        "The UAE has launched its first USD-backed stablecoin registered with the country’s central bank, "
        "marking a regulated entry into digital dollar issuance."
    )
    resp = client.post("/parse", json={"text": text})
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "STABLECOIN_ISSUANCE"


def test_jurisdiction_uae_maps_to_asia() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": "The UAE has launched its first USD-backed stablecoin registered with the country's central bank.",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["jurisdiction"] == "ASIA"


def test_jurisdiction_hong_kong_maps_to_asia() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": "Hong Kong regulators proposed new rules for licensed crypto exchanges.",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["jurisdiction"] == "ASIA"


def test_jurisdiction_russia_maps_to_europe() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": "Russia introduced new limits on crypto purchases for certain categories of buyers.",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["jurisdiction"] == "EUROPE"


def test_parse_invalid_json_returns_400() -> None:
    resp = client.post(
        "/parse",
        content=b"{not valid json}",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_parse_non_json_content_type_returns_415() -> None:
    resp = client.post(
        "/parse",
        content=b"text=hello",
        headers={"Content-Type": "text/plain"},
    )
    assert resp.status_code == 415
    assert "error" in resp.json()
