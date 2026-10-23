"""Unit Tests for Timeout Handling."""

import pytest
import httpx
from backend.app.services.link_validation_service import LinkValidationService


@pytest.mark.asyncio
async def test_timeout_classification(monkeypatch):
    service = LinkValidationService()

    class FakeTimeoutClient:
        def stream(self, method, url):
            raise httpx.ReadTimeout("Read timed out after 10 seconds")

        async def aclose(self):
            pass

    monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: FakeTimeoutClient())

    result = await service._execute_http_validation(
        url="https://slow-service.example.com",
        target_norm="https://slow-service.example.com",
        headers={},
    )

    assert result.status == "TIMEOUT"
    assert result.status_code is None
    assert "timed out" in result.error_message.lower()
