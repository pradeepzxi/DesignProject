"""Unit Tests for Invalid URLs and SSRF Blocking."""

import pytest
from backend.app.core.ssrf import validate_url_security
from backend.app.services.link_validation_service import LinkValidationService


def test_ssrf_blocking_private_ips():
    is_safe, reason = validate_url_security("http://127.0.0.1/admin")
    assert is_safe is False

    is_safe, reason = validate_url_security("http://10.0.0.5/secrets")
    assert is_safe is False

    is_safe, reason = validate_url_security("http://192.168.1.1/router")
    assert is_safe is False

    is_safe, reason = validate_url_security("http://169.254.169.254/latest/meta-data/")
    assert is_safe is False


def test_ssrf_blocking_internal_domains():
    is_safe, reason = validate_url_security("http://service.corp.local/api")
    assert is_safe is False
    assert "restricted" in reason.lower()


@pytest.mark.asyncio
async def test_validation_service_rejects_ssrf():
    service = LinkValidationService()
    result = await service.validate_url("http://127.0.0.1:8080/internal")
    assert result.status == "INVALID_URL"
    assert "SSRF Protection triggered" in result.error_message
