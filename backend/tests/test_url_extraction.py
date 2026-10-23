"""Unit Tests for URL Extraction and Filtering."""

from backend.app.utils.url_utils import is_valid_url_syntax, extract_url_tokens


def test_is_valid_url_syntax():
    assert is_valid_url_syntax("https://example.com") is True
    assert is_valid_url_syntax("http://sub.domain.org/path?q=1") is True
    assert is_valid_url_syntax("ftp://files.example.com") is False
    assert is_valid_url_syntax("javascript:alert(1)") is False
    assert is_valid_url_syntax("just a text line") is False
    assert is_valid_url_syntax("") is False
    assert is_valid_url_syntax(None) is False


def test_extract_url_tokens():
    url = "https://example.com/hr/leave/leave-policy-2024.pdf?dept=finance"
    tokens = extract_url_tokens(url)

    assert tokens["domain"] == "example.com"
    assert tokens["filename"] == "leave-policy-2024.pdf"
    assert "hr" in tokens["path_segments"]
    assert "leave" in tokens["path_segments"]
    assert "dept" in tokens["query_keys"]
    assert "policy" in tokens["terms"]
