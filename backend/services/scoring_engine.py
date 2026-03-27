"""
Scoring Engine
Implements CVSS v3.1-inspired vulnerability severity scoring.
"""

import logging
from typing import Dict, Optional, List

from backend.core.logger import pipeline_logger

logger = logging.getLogger(__name__)


def calculate_score(
    static_results: Optional[Dict] = None,
    dynamic_results: Optional[Dict] = None,
    execution_result: Optional[Dict] = None,
    patch_info: Optional[Dict] = None,
    analysis_id=None,
) -> Dict:
    """
    Calculate CVSS v3.1-inspired vulnerability severity score.

    Components:
        Static scan:  0-4 points
        Dynamic scan: 0-3 points
        Sandbox exec: 0-2 points
        Patch avail:  0-1 point

    Returns:
        {
            score: float (0-10),
            severity: str,
            component_breakdown: {...},
            recommendations: [str, ...]
        }
    """
    pipeline_logger.info(
        "Calculating vulnerability score",
        stage="SCORING",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    static_score = 0.0
    dynamic_score = 0.0
    execution_score = 0.0
    patch_score = 0.0
    recommendations = []

    # --- Static scan component (0-4 points) ---
    if static_results:
        sev = static_results.get("severity_breakdown", {})
        high_count = sev.get("high", 0) + sev.get("critical", 0)
        medium_count = sev.get("medium", 0)
        total_issues = static_results.get("total_issues", 0)

        if high_count > 5:
            static_score = 4.0
            recommendations.append("CRITICAL: Multiple high-severity static analysis findings require immediate remediation")
        elif high_count > 0:
            static_score = 2.5
            recommendations.append("HIGH: Static analysis found high-severity issues — review and fix identified vulnerabilities")
        elif medium_count > 5:
            static_score = 1.5
            recommendations.append("MEDIUM: Several medium-severity findings detected — schedule remediation")
        elif total_issues > 0:
            static_score = 0.5
            recommendations.append("LOW: Minor static analysis findings — consider addressing in next sprint")

        if medium_count > 10:
            static_score = min(static_score + 1.5, 4.0)
            recommendations.append("Excessive medium-severity findings indicate systemic code quality issues")

    # --- Dynamic scan component (0-3 points) ---
    if dynamic_results:
        sev = dynamic_results.get("severity_counts", {})
        critical = sev.get("critical", 0)
        high = sev.get("high", 0)
        indicators = dynamic_results.get("behavioral_indicators", [])

        if critical > 0:
            dynamic_score = 3.0
            recommendations.append("CRITICAL: Dynamic analysis confirmed critical-severity vulnerability in runtime behavior")
        elif high > 0:
            dynamic_score = 2.0
            recommendations.append("HIGH: Dynamic analysis detected high-severity behavioral patterns")
        elif len(indicators) > 0:
            dynamic_score = 1.0
            recommendations.append("MEDIUM: Behavioral indicators suggest potential runtime issues")

    # --- Sandbox execution component (0-2 points) ---
    if execution_result:
        vuln_confirmed = execution_result.get("vulnerabilities_confirmed", 0)
        total_tested = execution_result.get("total_exploits_tested", 0)
        success_rate = execution_result.get("success_rate", 0.0)

        if vuln_confirmed > 0 and success_rate > 0.5:
            execution_score = 2.0
            recommendations.append("CRITICAL: Exploit successfully executed — vulnerability is actively exploitable")
        elif vuln_confirmed > 0:
            execution_score = 1.5
            recommendations.append("HIGH: Exploit partially succeeded — vulnerability is likely exploitable under certain conditions")
        elif total_tested > 0 and success_rate > 0:
            execution_score = 1.0
            recommendations.append("MEDIUM: Some exploit attempts showed partial success")
        elif total_tested > 0:
            execution_score = 0.0
            recommendations.append("LOW: All exploit attempts failed — vulnerability may not be directly exploitable")

    # --- Patch availability component (0-1 point) ---
    if patch_info:
        patches_available = patch_info.get("patches_available", False)
        if not patches_available:
            patch_score = 1.0
            recommendations.append("WARNING: No known patch available — consider implementing custom mitigation")
        else:
            patch_score = 0.0
            recommendations.append("INFO: Patches are available — apply the recommended fix")

    # --- Calculate final score ---
    base_score = static_score + dynamic_score + execution_score + patch_score
    final_score = min(base_score, 10.0)
    final_score = round(final_score, 1)

    # Determine severity
    if final_score >= 9.0:
        severity = "CRITICAL"
    elif final_score >= 7.0:
        severity = "HIGH"
    elif final_score >= 4.0:
        severity = "MEDIUM"
    elif final_score > 0.0:
        severity = "LOW"
    else:
        severity = "NONE"

    # Priority-sort recommendations
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "WARNING": 3, "LOW": 4, "INFO": 5}
    recommendations.sort(
        key=lambda r: priority_order.get(r.split(":")[0], 99)
    )

    component_breakdown = {
        "static_scan": {"score": static_score, "max": 4.0},
        "dynamic_scan": {"score": dynamic_score, "max": 3.0},
        "exploit_execution": {"score": execution_score, "max": 2.0},
        "patch_availability": {"score": patch_score, "max": 1.0},
    }

    pipeline_logger.info(
        f"Score={final_score}, Severity={severity} (static={static_score}, dynamic={dynamic_score}, exec={execution_score}, patch={patch_score})",
        stage="SCORING",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    return {
        "score": final_score,
        "severity": severity,
        "component_breakdown": component_breakdown,
        "recommendations": recommendations,
        "cvss_vector": _generate_cvss_vector(
            static_score, dynamic_score, execution_score
        ),
        "exploitability": min(1.0, (execution_score + dynamic_score) / 5.0),
        "impact_score": min(1.0, (static_score + dynamic_score) / 7.0),
        "confidence": _calculate_confidence(
            static_results, dynamic_results, execution_result
        ),
    }


def _generate_cvss_vector(static: float, dynamic: float, execution: float) -> str:
    """Generate a simplified CVSS v3.1 vector string."""
    av = "N" if execution > 1.0 else "A"  # Network vs Adjacent
    ac = "L" if static > 2.0 else "H"  # Low or High complexity
    pr = "N" if execution > 0 else "L"  # Privileges required
    ui = "N"  # User interaction
    s = "U"  # Scope unchanged
    c = "H" if dynamic > 2.0 else "L"  # Confidentiality
    i = "H" if execution > 1.0 else "L"  # Integrity
    a = "H" if static > 3.0 else "N"  # Availability

    return f"AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"


def _calculate_confidence(
    static_results: Optional[Dict],
    dynamic_results: Optional[Dict],
    execution_result: Optional[Dict],
) -> float:
    """Calculate overall confidence in the scoring (0.0-1.0)."""
    confidence = 0.3  # Base

    if static_results and static_results.get("total_issues", 0) > 0:
        confidence += 0.2

    if dynamic_results and dynamic_results.get("findings"):
        confidence += 0.2

    if execution_result and execution_result.get("total_exploits_tested", 0) > 0:
        confidence += 0.3

    return min(1.0, confidence)
