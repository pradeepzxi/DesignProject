"""Unit Tests for URL Normalization and Canonicalization."""

import pytest
from backend.app.utils.url_utils import normalize_url, is_valid_url_syntax, extract_url_tokens


def test_url_normalization_basic():
    raw = "  HTTP://EXAMPLE.COM/index.html  "
    normalized = normalize_url(raw)
    assert normalized == "http://example.com/index.html"


def test_url_normalization_strips_tracking_params():
    raw = "https://example.com/doc.pdf?utm_source=newsletter&utm_medium=email&utm_campaign=spring&version=2"
    normalized = normalize_url(raw)
    assert "utm_source" not in normalized
    assert "utm_medium" not in normalized
    assert "utm_campaign" not in normalized
    assert "version=2" in normalized
    assert normalized == "https://example.com/doc.pdf?version=2"


def test_url_normalization_removes_default_ports():
    raw_http = "http://example.com:80/path"
    raw_https = "https://example.com:443/path"
    assert normalize_url(raw_http) == "http://example.com/path"
    assert normalize_url(raw_https) == "https://example.com/path"


def test_url_normalization_cleans_punctuation_artifacts():
    raw = '"https://example.com/policy.pdf",'
    assert normalize_url(raw) == "https://example.com/policy.pdf"


def test_malformed_url_raises_error():
    with pytest.raises(ValueError):
        normalize_url("not_a_valid_url")

    with pytest.raises(ValueError):
        normalize_url("")
