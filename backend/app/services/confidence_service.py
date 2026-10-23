"""Confidence Decision Engine.

Evaluates candidate confidence thresholds and applies strict security and accessibility
safeguards to determine autonomous remediation vs human-in-the-loop review routing.
"""

from typing import Dict, Any, Optional, Tuple
from backend.app.core.ssrf import validate_url_security
from backend.app.core.logging_config import logger

AUTO_REPAIR_THRESHOLD = 0.90
HUMAN_REVIEW_THRESHOLD = 0.65


class ConfidenceService:
    def __init__(
        self,
        auto_repair_threshold: float = AUTO_REPAIR_THRESHOLD,
        human_review_threshold: float = HUMAN_REVIEW_THRESHOLD,
    ):
        self.auto_repair_threshold = auto_repair_threshold
        self.human_review_threshold = human_review_threshold

    def evaluate_candidate(
        self,
        broken_url: str,
        top_candidate: Optional[Dict[str, Any]],
    ) -> Tuple[str, float, str]:
        """Determine routing decision and check safety preconditions.

        Returns:
            (decision, confidence_score, reason)
            decision: "AUTO_REPAIR" | "HUMAN_REVIEW" | "NO_REPLACEMENT"
        """
        if not top_candidate:
            return "NO_REPLACEMENT", 0.0, "No candidate replacements were discovered for this broken link."

        cand_url = top_candidate.get("candidate_url", "")
        score = top_candidate.get("overall_score", 0.0)

        # 1. Safeguard: Non-identical URL
        if cand_url.strip().lower() == broken_url.strip().lower():
            return "NO_REPLACEMENT", score, "Candidate URL is identical to the broken URL."

        # 2. Quality Floor: Low confidence rejects without triage
        if score < self.human_review_threshold:
            return (
                "NO_REPLACEMENT",
                score,
                f"Low confidence ({round(score * 100, 1)}% < {round(self.human_review_threshold * 100)}%); candidate does not meet minimum quality threshold.",
            )

        # 3. Safeguard: SSRF Security Check
        is_safe, sec_reason = validate_url_security(cand_url, enforce=False)
        if not is_safe:
            return "HUMAN_REVIEW", score, f"Candidate blocked by security policy: {sec_reason}"

        # 4. Safeguard: Candidate Accessibility
        is_accessible = top_candidate.get("is_accessible", True)
        http_status = top_candidate.get("http_status")
        if not is_accessible or (http_status and http_status >= 400):
            return "HUMAN_REVIEW", score, f"Candidate target responded with error status HTTP {http_status}."

        # 5. Threshold Routing
        if score >= self.auto_repair_threshold:
            return (
                "AUTO_REPAIR",
                score,
                f"High confidence ({round(score * 100, 1)}% >= {round(self.auto_repair_threshold * 100)}%) with all safety preconditions satisfied.",
            )
        else:
            return (
                "HUMAN_REVIEW",
                score,
                f"Moderate confidence ({round(score * 100, 1)}%); queued for human review and approval.",
            )


confidence_engine = ConfidenceService()
