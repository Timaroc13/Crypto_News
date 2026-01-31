from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import crypto_news_parser.main as main_mod
from crypto_news_parser.fetch import (
    FetchBlockedError,
    FetchResult,
    FetchTimeoutError,
    FetchTooLargeError,
    FetchUnsupportedContentTypeError,
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(main_mod.app)


def test_parse_url_success(monkeypatch, client: TestClient) -> None:
    async def fake_fetch(url: str) -> FetchResult:
        return FetchResult(
            url=url,
            content_type="text/html",
            text="The U.S. SEC clarified new crypto rules for tokenized stocks.",
        )

    monkeypatch.setattr(main_mod, "fetch_url_text", fake_fetch)

    resp = client.post("/parse_url", json={"url": "https://example.com/a"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_type"] == "LEGISLATION_POLICY_DEVELOPMENT"
    assert data["jurisdiction"] == "US"


def test_parse_url_blocked(monkeypatch, client: TestClient) -> None:
    async def fake_fetch(url: str):
        raise FetchBlockedError("Blocked destination")

    monkeypatch.setattr(main_mod, "fetch_url_text", fake_fetch)

    resp = client.post("/parse_url", json={"url": "https://127.0.0.1/"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "URL_BLOCKED"


def test_parse_url_too_large(monkeypatch, client: TestClient) -> None:
    async def fake_fetch(url: str):
        raise FetchTooLargeError("too big")

    monkeypatch.setattr(main_mod, "fetch_url_text", fake_fetch)

    resp = client.post("/parse_url", json={"url": "https://example.com/large"})
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "FETCH_TOO_LARGE"


def test_parse_url_timeout(monkeypatch, client: TestClient) -> None:
    async def fake_fetch(url: str):
        raise FetchTimeoutError("timeout")

    monkeypatch.setattr(main_mod, "fetch_url_text", fake_fetch)

    resp = client.post("/parse_url", json={"url": "https://example.com/slow"})
    assert resp.status_code == 504
    assert resp.json()["error"]["code"] == "FETCH_TIMEOUT"


def test_parse_url_unsupported_content_type(monkeypatch, client: TestClient) -> None:
    async def fake_fetch(url: str):
        raise FetchUnsupportedContentTypeError("pdf")

    monkeypatch.setattr(main_mod, "fetch_url_text", fake_fetch)

    resp = client.post("/parse_url", json={"url": "https://example.com/doc.pdf"})
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "UNSUPPORTED_FETCH_CONTENT_TYPE"


def test_parse_url_empty_extracted_text_returns_422(monkeypatch, client: TestClient) -> None:
    async def fake_fetch(url: str) -> FetchResult:
        return FetchResult(url=url, content_type="text/html", text="")

    monkeypatch.setattr(main_mod, "fetch_url_text", fake_fetch)

    resp = client.post("/parse_url", json={"url": "https://example.com/empty"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "INVALID_REQUEST"
