from collections.abc import AsyncIterator
from typing import Any, Iterator

import httpx
import pytest

from app.src.ip_detector import PublicIPDetector


class DummyResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "https://example.com"),
                response=httpx.Response(self.status_code),
            )


class DummyAsyncClient:
    def __init__(self, results: Iterator[Any]) -> None:
        self._results = results

    async def __aenter__(self) -> "DummyAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str) -> DummyResponse:
        result = next(self._results)
        if isinstance(result, Exception):
            raise result
        return result


def patch_httpx(monkeypatch: pytest.MonkeyPatch, responses: list[Any]) -> None:
    iterator = iter(responses)

    def factory(*args: Any, **kwargs: Any) -> DummyAsyncClient:
        return DummyAsyncClient(iterator)

    monkeypatch.setattr("app.src.ip_detector.httpx.AsyncClient", factory)


@pytest.mark.asyncio
async def test_ip_detector_returns_first_success(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_httpx(monkeypatch, [DummyResponse("1.2.3.4")])
    detector = PublicIPDetector()

    ip = await detector.get_current_ip()

    assert ip == "1.2.3.4"


@pytest.mark.asyncio
async def test_ip_detector_falls_back_to_next_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_httpx(
        monkeypatch,
        [
            DummyResponse("error", status_code=500),
            httpx.HTTPError("boom"),
            DummyResponse("5.6.7.8"),
        ],
    )
    detector = PublicIPDetector()

    ip = await detector.get_current_ip()

    assert ip == "5.6.7.8"


@pytest.mark.asyncio
async def test_ip_detector_parses_cloudflare_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    trace = "fl=1\nip=9.9.9.9\n"
    patch_httpx(monkeypatch, [DummyResponse(trace)])
    detector = PublicIPDetector()
    detector._providers = ["https://1.1.1.1/cdn-cgi/trace"]

    ip = await detector.get_current_ip()

    assert ip == "9.9.9.9"


@pytest.mark.asyncio
async def test_ip_detector_raises_when_all_providers_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_httpx(
        monkeypatch,
        [
            httpx.HTTPError("boom"),
            DummyResponse("bad", status_code=500),
            ValueError("parse error"),
            httpx.HTTPError("boom"),
        ],
    )
    detector = PublicIPDetector()

    with pytest.raises(RuntimeError):
        await detector.get_current_ip()


@pytest.mark.asyncio
async def test_ip_detector_raises_when_trace_missing_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_httpx(monkeypatch, [DummyResponse("fl=1\nno-ip-here\n")])
    detector = PublicIPDetector()
    detector._providers = ["https://1.1.1.1/cdn-cgi/trace"]

    with pytest.raises(RuntimeError):
        await detector.get_current_ip()

