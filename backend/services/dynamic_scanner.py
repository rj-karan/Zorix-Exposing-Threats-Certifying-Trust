"""
Dynamic Scanner Service
Performs behavioral analysis and dynamic scanning on execution results.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional, List

from backend.config import get_settings
from backend.core.logger import pipeline_logger

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_dynamic_scan(
    execution_result: Optional[Dict] = None,
    snapshot_path: Optional[str] = None,
    analysis_id=None,
) -> Dict:
    """
    Run dynamic analysis on execution results.

    Since we execute in isolated sandboxes without exposed services,
    this primarily performs behavioral analysis on execution logs.

    Args:
        execution_result: Dict with stdout, stderr, exit_code from sandbox
        snapshot_path: Path to the code snapshot
        analysis_id: For logging context

    Returns:
        {
            findings: [...],
            severity_counts: { critical, high, medium, low },
            behavioral_indicators: [...],
        }
    """
    pipeline_logger.info(
        "Starting dynamic scan / behavioral analysis",
        stage="SCANNING_DYNAMIC",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    findings = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    behavioral_indicators = []

    # Analyze execution logs for suspicious patterns
    if execution_result:
        log_findings = _analyze_execution_logs(execution_result)
        findings.extend(log_findings.get("findings", []))
        behavioral_indicators.extend(log_findings.get("indicators", []))
        for k in severity_counts:
            severity_counts[k] += log_findings.get("severity_counts", {}).get(k, 0)

    # Analyze snapshot for runtime vulnerability patterns
    if snapshot_path:
        runtime_findings = _analyze_runtime_patterns(snapshot_path)
        findings.extend(runtime_findings.get("findings", []))
        for k in severity_counts:
            severity_counts[k] += runtime_findings.get("severity_counts", {}).get(k, 0)

    pipeline_logger.info(
        f"Dynamic scan found {len(findings)} findings, {len(behavioral_indicators)} behavioral indicators",
        stage="SCANNING_DYNAMIC",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    return {
        "findings": findings,
        "severity_counts": severity_counts,
        "behavioral_indicators": behavioral_indicators,
    }


def _analyze_execution_logs(execution_result: Dict) -> Dict:
    """Analyze sandbox execution logs for suspicious behavior."""
    stdout = execution_result.get("stdout", "") or ""
    stderr = execution_result.get("stderr", "") or ""
    exit_code = execution_result.get("exit_code", -1)
    combined = f"{stdout}\n{stderr}".lower()

    findings = []
    indicators = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    # Pattern checks
    suspicious_patterns = [
        {
            "pattern": r"vulnerable",
            "severity": "HIGH",
            "message": "Exploit execution confirmed vulnerability",
            "indicator": "Vulnerability confirmed by sandbox execution",
        },
        {
            "pattern": r"injection successful",
            "severity": "HIGH",
            "message": "Injection attack was successful",
            "indicator": "Injection vector is exploitable",
        },
        {
            "pattern": r"retrieved data",
            "severity": "HIGH",
            "message": "Data exfiltration detected during exploit execution",
            "indicator": "Data leakage through injection",
        },
        {
            "pattern": r"permission denied|access denied",
            "severity": "LOW",
            "message": "Access control properly blocked the exploit",
            "indicator": "Access controls are functioning",
        },
        {
            "pattern": r"segfault|segmentation fault",
            "severity": "HIGH",
            "message": "Memory corruption detected — possible buffer overflow",
            "indicator": "Memory safety violation",
        },
        {
            "pattern": r"stack smashing detected",
            "severity": "CRITICAL",
            "message": "Stack buffer overflow detected",
            "indicator": "Stack-based buffer overflow exploitable",
        },
        {
            "pattern": r"connection refused|connection reset",
            "severity": "LOW",
            "message": "Network isolation confirmed — sandbox blocked network access",
            "indicator": "Network isolation working",
        },
        {
            "pattern": r"<script>|javascript:|onclick=",
            "severity": "MEDIUM",
            "message": "XSS payload reflective patterns detected in output",
            "indicator": "Potential XSS vulnerability",
        },
    ]

    for pat in suspicious_patterns:
        if re.search(pat["pattern"], combined):
            sev = pat["severity"].lower()
            severity_counts[sev] += 1
            findings.append({
                "tool": "dynamic-behavioral",
                "severity": pat["severity"],
                "message": pat["message"],
                "type": "behavioral",
            })
            indicators.append(pat["indicator"])

    # Exit code analysis
    if exit_code == 0 and "vulnerable" in combined:
        indicators.append("Exploit exited successfully — vulnerability likely exploitable")
    elif exit_code != 0:
        indicators.append(f"Exploit exited with code {exit_code}")

    # Execution time analysis
    exec_time = execution_result.get("execution_time_ms", 0)
    if exec_time and exec_time > 30000:
        indicators.append(f"Long execution time ({exec_time}ms) — possible time-based exploit")
        severity_counts["medium"] += 1
        findings.append({
            "tool": "dynamic-behavioral",
            "severity": "MEDIUM",
            "message": f"Suspicious execution time: {exec_time}ms",
            "type": "timing",
        })

    return {
        "findings": findings,
        "indicators": indicators,
        "severity_counts": severity_counts,
    }


def _analyze_runtime_patterns(snapshot_path: str) -> Dict:
    """Analyze code for runtime vulnerability patterns."""
    findings = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    runtime_patterns = {
        "requests.get(": ("MEDIUM", "HTTP request without SSL verification check"),
        "verify=False": ("HIGH", "SSL verification disabled"),
        "debug=True": ("MEDIUM", "Debug mode enabled in production code"),
        "CORS(app)": ("MEDIUM", "Wide-open CORS policy"),
        "allow_origins=['*']": ("HIGH", "CORS allows all origins"),
        "logging.disable": ("LOW", "Logging disabled — may hide security events"),
    }

    snap = Path(snapshot_path)
    for ext in ("*.py", "*.js", "*.ts"):
        for fpath in snap.rglob(ext):
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                for line_no, line in enumerate(content.splitlines(), 1):
                    for pattern, (sev, msg) in runtime_patterns.items():
                        if pattern in line:
                            severity_counts[sev.lower()] += 1
                            findings.append({
                                "tool": "dynamic-pattern",
                                "file": str(fpath.relative_to(snap)),
                                "line": line_no,
                                "severity": sev,
                                "message": msg,
                                "type": "runtime_pattern",
                            })
            except Exception:
                continue

    return {"findings": findings, "severity_counts": severity_counts}
