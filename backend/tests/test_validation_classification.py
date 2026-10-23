"""Unit Tests for Link Validation Engine Status Classification."""

from backend.app.services.link_validation_service import LinkValidationService


def test_classify_status_codes():
    service = LinkValidationService()

    # Successful
    assert service.classify_status(status_code=200, is_redirect=False, redirect_count=0) == "VALID"
    assert service.classify_status(status_code=204, is_redirect=False, redirect_count=0) == "VALID"

    # Redirect
    assert service.classify_status(status_code=301, is_redirect=True, redirect_count=1) == "REDIRECT"
    assert service.classify_status(status_code=302, is_redirect=True, redirect_count=1) == "REDIRECT"

    # Client Errors
    assert service.classify_status(status_code=404, is_redirect=False, redirect_count=0) == "BROKEN_404"
    assert service.classify_status(status_code=403, is_redirect=False, redirect_count=0) == "FORBIDDEN"
    assert service.classify_status(status_code=401, is_redirect=False, redirect_count=0) == "UNAUTHORIZED"
    assert service.classify_status(status_code=410, is_redirect=False, redirect_count=0) == "BROKEN_4XX"
    assert service.classify_status(status_code=429, is_redirect=False, redirect_count=0) == "BROKEN_4XX"

    # Server Errors
    assert service.classify_status(status_code=500, is_redirect=False, redirect_count=0) == "SERVER_ERROR_5XX"
    assert service.classify_status(status_code=502, is_redirect=False, redirect_count=0) == "SERVER_ERROR_5XX"
    assert service.classify_status(status_code=503, is_redirect=False, redirect_count=0) == "SERVER_ERROR_5XX"

    # Network / System Failures
    assert service.classify_status(status_code=None, is_redirect=False, redirect_count=0, error_type="TIMEOUT") == "TIMEOUT"
    assert service.classify_status(status_code=None, is_redirect=False, redirect_count=0, error_type="DNS_ERROR") == "DNS_ERROR"
    assert service.classify_status(status_code=None, is_redirect=False, redirect_count=0, error_type="CONNECTION_ERROR") == "CONNECTION_ERROR"
    assert service.classify_status(status_code=None, is_redirect=False, redirect_count=0, error_type="INVALID_URL") == "INVALID_URL"
