from fastapi.testclient import TestClient

from crypto_news_parser.main import app

client = TestClient(app)


def test_parse_returns_schema_fields() -> None:
    resp = client.post(
        "/parse",
        json={"text": "BlackRock’s Bitcoin ETF saw $400M in inflows after SEC approval."},
    )
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
        "The UAE has launched its first USD-backed stablecoin registered "
        "with the country’s central bank, "
        "marking a regulated entry into digital dollar issuance."
    )
    resp = client.post("/parse", json={"text": text})
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "STABLECOIN_ISSUANCE"


def test_jurisdiction_uae_maps_to_asia() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": (
                "The UAE has launched its first USD-backed stablecoin registered "
                "with the country's central bank."
            ),
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
            "text": (
                "Russia introduced new limits on crypto purchases for certain categories of buyers."
            ),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["jurisdiction"] == "EUROPE"


def test_entities_extract_osl_group() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": (
                "OSL Group raised $200 million to expand its stablecoin-based payments "
                "infrastructure."
            ),
        },
    )
    assert resp.status_code == 200
    assert "OSL Group" in resp.json()["entities"]


def test_entities_extract_person_name() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": (
                "Michael Saylor’s firm Strategy purchased an additional $2.13 billion "
                "worth of bitcoin."
            ),
        },
    )
    assert resp.status_code == 200
    assert "Michael Saylor" in resp.json()["entities"]


def test_entities_extract_single_word_entity_allowlist() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": (
                "Crypto exchange Bybit plans to roll out IBAN accounts and neobank-style features."
            ),
        },
    )
    assert resp.status_code == 200
    assert "Bybit" in resp.json()["entities"]


def test_assets_extract_bitcoin_to_btc() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": "Bitcoin briefly fell below $90,000 amid a broader global market sell-off.",
        },
    )
    assert resp.status_code == 200
    assert "BTC" in resp.json()["assets"]


def test_assets_extract_solana_possessive_to_sol() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": "Solana’s validator count has fallen roughly 68% from its 2023 peak.",
        },
    )
    assert resp.status_code == 200
    assert "SOL" in resp.json()["assets"]


def test_assets_do_not_include_unrelated_uppercase_tokens() -> None:
    resp = client.post(
        "/parse",
        json={
            "text": "OSL Group raised $200 million and the CEO outlined the plan.",
        },
    )
    assert resp.status_code == 200
    assets = resp.json()["assets"]
    assert "OSL" not in assets
    assert "CEO" not in assets


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
