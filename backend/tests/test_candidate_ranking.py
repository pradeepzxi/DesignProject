"""Tests for Candidate Discovery, Semantic Similarity, and Hybrid Ranking."""

import pytest
from backend.app.services.candidate_provider import LocalCandidateProvider
from backend.app.services.semantic_similarity_service import similarity_service
from backend.app.services.candidate_ranking_service import ranking_service, DEFAULT_WEIGHTS


@pytest.mark.asyncio
async def test_query_variation_generation():
    provider = LocalCandidateProvider()
    context = {
        "document_title": "Enterprise Cybersecurity Architecture",
        "section_heading": "VPN Connectivity Standard",
        "anchor_text": "Download GlobalProtect Client",
        "keywords": ["vpn", "globalprotect", "client", "security"],
        "url_tokens": {
            "domain": "vpn.corp.local",
            "filename": "gp-client-setup.exe",
            "path_segments": ["downloads", "software"],
        },
    }
    variations = provider.generate_query_variations(
        broken_url="https://vpn.corp.local/downloads/software/gp-client-setup.exe",
        anchor_text="Download GlobalProtect Client",
        context=context,
    )

    assert len(variations) >= 3
    assert any("globalprotect" in v.lower() for v in variations)
    assert any("vpn" in v.lower() for v in variations)


@pytest.mark.asyncio
async def test_candidate_discovery_offline():
    provider = LocalCandidateProvider()
    context = {
        "document_title": "HR Leave Policy",
        "section_heading": "Statutory Absence",
        "anchor_text": "Statutory Sick Leave Schedule",
        "keywords": ["leave", "sick", "absence", "statutory"],
    }
    candidates = await provider.discover_candidates(
        broken_url="http://intranet.corp/hr/old-leave-system.php",
        anchor_text="Statutory Sick Leave Schedule",
        context=context,
        max_candidates=5,
    )

    assert len(candidates) > 0
    top = candidates[0]
    assert top.candidate_url.startswith("http")
    assert any("leave" in c.page_title.lower() or "absence" in c.candidate_url.lower() for c in candidates)


@pytest.mark.asyncio
async def test_semantic_similarity_range():
    context = {
        "document_title": "HR Leave Policy",
        "section_heading": "Sick Leave",
        "anchor_text": "Standard Sick Leave Guidelines",
        "surrounding_text": "Employees must submit sick leave documentation within three days of return.",
    }
    cand_text = "Official 2024 absence and sick leave procedure for all enterprise staff members."
    cand_title = "2024 Leave and Absence Standard"

    sim = await similarity_service.compute_similarity(context, cand_text, cand_title)
    assert 0.0 <= sim <= 1.0
    assert sim > 0.4  # Semantically aligned text should score high


def test_title_similarity_containment():
    sim = similarity_service.calculate_title_similarity(
        anchor_text="VPN Client",
        section_heading="Remote Tools",
        candidate_title="GlobalConnect Enterprise VPN Client & Setup Guide",
    )
    assert 0.0 <= sim <= 1.0
    assert sim >= 0.8  # Containment overlap should recognize subphrase match


def test_url_similarity_tokens():
    sim = similarity_service.calculate_url_similarity(
        broken_url="https://intranet.corp/vpn/client-v1.exe",
        candidate_url="https://intranet.corp/vpn/client-v2.exe",
    )
    assert 0.0 <= sim <= 1.0
    assert sim > 0.6  # High path token overlap


def test_composite_ranking_weights():
    features = {
        "semantic_similarity": 0.90,
        "title_similarity": 0.80,
        "url_similarity": 0.70,
        "keyword_overlap": 0.85,
        "domain_score": 1.00,
        "content_quality_score": 1.00,
    }
    score = ranking_service.calculate_overall_score(features, DEFAULT_WEIGHTS)
    assert 0.0 <= score <= 1.0
    # Expected: 0.4*0.9 + 0.2*0.8 + 0.15*0.7 + 0.1*0.85 + 0.1*1.0 + 0.05*1.0 = 0.36 + 0.16 + 0.105 + 0.085 + 0.10 + 0.05 = 0.86
    assert 0.85 <= score <= 0.88


def test_explainable_recommendation_generation():
    features = {
        "semantic_similarity": 0.92,
        "title_similarity": 0.88,
        "url_similarity": 0.75,
        "keyword_overlap": 0.80,
        "domain_score": 1.00,
        "content_quality_score": 1.00,
    }
    explanation = ranking_service.generate_explanation(
        features=features,
        rank=1,
        context={"anchor_text": "VPN Client"},
        candidate_title="Enterprise VPN Guide",
    )
    assert "semantic" in explanation.lower()
    assert "domain" in explanation.lower()
    assert len(explanation) > 30
