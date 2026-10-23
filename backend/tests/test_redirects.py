"""Unit Tests for Redirect Handling."""

import pytest
from backend.app.services.link_validation_service import LinkValidationService


def test_redirect_classification():
    service = LinkValidationService()
    # 301 Permanent Redirect
    assert service.classify_status(status_code=301, is_redirect=True, redirect_count=1) == "REDIRECT"
    # 302 Found
    assert service.classify_status(status_code=302, is_redirect=True, redirect_count=1) == "REDIRECT"
    # Redirect loop or hops
    assert service.classify_status(status_code=308, is_redirect=True, redirect_count=3) == "REDIRECT"


@pytest.mark.asyncio
async def test_redirect_validation_simulation(monkeypatch):
    service = LinkValidationService()

    class FakeResponse:
        status_code = 200
        url = "https://example.com/new-final-location"
        history = [1, 2]  # 2 redirects
        headers = {"content-type": "text/html"}

    class FakeStreamContext:
        async def __aenter__(self):
            return FakeResponse()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class FakeClient:
        def stream(self, method, url):
            return FakeStreamContext()

        async def aclose(self):
            pass

    monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: FakeClient())

    result = await service._execute_http_validation(
        url="http://example.com/old-location",
        target_norm="http://example.com/old-location",
        headers={},
    )

    assert result.status == "REDIRECT"
    assert result.redirect_count == 2
    assert result.final_url == "https://example.com/new-final-location"
