"""Tests for Confidence Engine and Safety Safeguards."""

import pytest
from backend.app.services.confidence_service import ConfidenceService


def test_confidence_threshold_auto_repair():
    engine = ConfidenceService(auto_repair_threshold=0.90, human_review_threshold=0.65)
    top_cand = {
        "candidate_url": "https://example.com/valid-page",
        "overall_score": 0.94,
        "is_accessible": True,
        "http_status": 200,
    }
    decision, conf, reason = engine.evaluate_candidate(
        broken_url="https://example.com/broken-link",
        top_candidate=top_cand,
    )
    assert decision == "AUTO_REPAIR"
    assert conf == 0.94
    assert "High confidence" in reason


def test_confidence_threshold_human_review():
    engine = ConfidenceService(auto_repair_threshold=0.90, human_review_threshold=0.65)
    top_cand = {
        "candidate_url": "https://example.com/valid-page",
        "overall_score": 0.74,
        "is_accessible": True,
        "http_status": 200,
    }
    decision, conf, reason = engine.evaluate_candidate(
        broken_url="https://example.com/broken-link",
        top_candidate=top_cand,
    )
    assert decision == "HUMAN_REVIEW"
    assert conf == 0.74
    assert "Moderate confidence" in reason


def test_confidence_threshold_no_replacement():
    engine = ConfidenceService(auto_repair_threshold=0.90, human_review_threshold=0.65)
    top_cand = {
        "candidate_url": "https://example.com/random-page",
        "overall_score": 0.45,
        "is_accessible": True,
        "http_status": 200,
    }
    decision, conf, reason = engine.evaluate_candidate(
        broken_url="https://example.com/broken-link",
        top_candidate=top_cand,
    )
    assert decision == "NO_REPLACEMENT"
    assert conf == 0.45


def test_safeguard_identical_url_blocked():
    engine = ConfidenceService()
    same_url = "https://example.com/page1"
    top_cand = {
        "candidate_url": same_url,
        "overall_score": 0.98,
        "is_accessible": True,
        "http_status": 200,
    }
    decision, conf, reason = engine.evaluate_candidate(
        broken_url=same_url,
        top_candidate=top_cand,
    )
    assert decision == "NO_REPLACEMENT"
    assert "identical" in reason.lower()


def test_safeguard_inaccessible_candidate_routes_to_human_review():
    engine = ConfidenceService()
    top_cand = {
        "candidate_url": "https://example.com/another-broken-link",
        "overall_score": 0.95,
        "is_accessible": False,
        "http_status": 404,
    }
    decision, conf, reason = engine.evaluate_candidate(
        broken_url="https://example.com/broken-link",
        top_candidate=top_cand,
    )
    assert decision == "HUMAN_REVIEW"
    assert "error status" in reason.lower() or "blocked" in reason.lower()
