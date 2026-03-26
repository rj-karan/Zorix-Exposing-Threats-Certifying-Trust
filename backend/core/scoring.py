import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for computing vulnerability severity scores (CVSS-like)."""

    def compute_score(
        self,
        confidence_score: float,
        severity: Optional[str] = None,
        affected_lines: int = 1,
    ) -> float:
        """
        Compute vulnerability severity score.

        Args:
            confidence_score: AI analysis confidence (0.0-1.0)
            severity: Manual severity level (critical, high, medium, low)
            affected_lines: Number of affected code lines

        Returns:
            Normalized severity score (0.0-10.0)
        """
        try:
            # Base score from confidence
            score = confidence_score * 10.0

            # Adjust for manual severity if provided
            if severity:
                severity_multipliers = {
                    "critical": 1.0,
                    "high": 0.85,
                    "medium": 0.65,
                    "low": 0.4,
                }
                multiplier = severity_multipliers.get(severity.lower(), 0.5)
                score = score * multiplier

            # Adjust for code spread (more lines affected = higher risk)
            spread_factor = min(1.0 + (affected_lines * 0.1), 1.5)
            score = score * spread_factor

            # Clamp to 0-10 range
            score = max(0.0, min(10.0, score))

            logger.info(
                f"Computed vulnerability score: {score:.2f} "
                f"(confidence: {confidence_score}, severity: {severity})"
            )

            return round(score, 2)

        except Exception as e:
            logger.error(f"Scoring error: {str(e)}")
            return 5.0  # Default neutral score


# Singleton instance
scoring_service = ScoringService()
