"""
Static Scanner Service
Runs Bandit and Semgrep static analysis on source code snapshots.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

from backend.config import get_settings
from backend.core.logger import pipeline_logger

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_static_scan(
    snapshot_path: str,
    scan_id: Optional[str] = None,
    analysis_id=None,
) -> Dict:
    """
    Run static analysis tools (Bandit + Semgrep) on the snapshot.

    Args:
        snapshot_path: Path to the code snapshot directory
        scan_id: Unique identifier for this scan
        analysis_id: For logging context

    Returns:
        {
            bandit_results: {...},
            semgrep_results: {...},
            total_issues: int,
            severity_breakdown: { critical, high, medium, low },
            findings: [...]
        }
    """
    pipeline_logger.info(
        f"Starting static scan on {snapshot_path}",
        stage="SCANNING_STATIC",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    bandit_results = {"findings": [], "severity_counts": {}}
    semgrep_results = {"findings": [], "severity_counts": {}}

    # Run Bandit
    if settings.BANDIT_ENABLED:
        try:
            bandit_results = await _run_bandit(snapshot_path, scan_id)
            pipeline_logger.info(
                f"Bandit found {len(bandit_results.get('findings', []))} issues",
                stage="SCANNING_STATIC",
                analysis_id=str(analysis_id) if analysis_id else None,
            )
        except Exception as e:
            logger.warning(f"Bandit scan failed: {e}")
            bandit_results = _bandit_fallback_analysis(snapshot_path)

    # Run Semgrep
    if settings.SEMGREP_ENABLED:
        try:
            semgrep_results = await _run_semgrep(snapshot_path, scan_id)
            pipeline_logger.info(
                f"Semgrep found {len(semgrep_results.get('findings', []))} issues",
                stage="SCANNING_STATIC",
                analysis_id=str(analysis_id) if analysis_id else None,
            )
        except Exception as e:
            logger.warning(f"Semgrep scan failed: {e}")
            semgrep_results = _semgrep_fallback_analysis(snapshot_path)

    # Aggregate severity counts
    severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for key in severity:
        severity[key] += bandit_results.get("severity_counts", {}).get(key, 0)
        severity[key] += semgrep_results.get("severity_counts", {}).get(key, 0)

    all_findings = bandit_results.get("findings", []) + semgrep_results.get("findings", [])

    return {
        "bandit_results": bandit_results,
        "semgrep_results": semgrep_results,
        "total_issues": len(all_findings),
        "severity_breakdown": severity,
        "findings": all_findings,
    }


async def _run_bandit(snapshot_path: str, scan_id: Optional[str]) -> Dict:
    """Run Bandit static analysis."""
    output_file = tempfile.mktemp(suffix=".json", prefix=f"bandit_{scan_id or 'scan'}_")

    try:
        result = subprocess.run(
            [settings.BANDIT_PATH, "-r", snapshot_path, "-f", "json", "-ll", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Bandit returns exit code 1 if it finds issues (that's normal)
        output = result.stdout
        if not output:
            return {"findings": [], "severity_counts": {}}

        data = json.loads(output)
        findings = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in data.get("results", []):
            sev = issue.get("issue_severity", "LOW").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

            findings.append({
                "tool": "bandit",
                "file": issue.get("filename", ""),
                "line": issue.get("line_number", 0),
                "severity": sev.upper(),
                "confidence": issue.get("issue_confidence", ""),
                "issue": issue.get("issue_text", ""),
                "test_id": issue.get("test_id", ""),
                "more_info": issue.get("more_info", ""),
            })

        return {"findings": findings, "severity_counts": severity_counts}

    except FileNotFoundError:
        logger.warning("Bandit not installed. Using fallback analysis.")
        return _bandit_fallback_analysis(snapshot_path)
    except subprocess.TimeoutExpired:
        logger.warning("Bandit scan timed out")
        return {"findings": [], "severity_counts": {}}
    except json.JSONDecodeError:
        logger.warning("Failed to parse Bandit output")
        return {"findings": [], "severity_counts": {}}


async def _run_semgrep(snapshot_path: str, scan_id: Optional[str]) -> Dict:
    """Run Semgrep static analysis."""
    # Check for custom rules
    custom_rules = Path("security/semgrep_rules.yaml")
    config = str(custom_rules) if custom_rules.exists() else "auto"

    try:
        result = subprocess.run(
            [settings.SEMGREP_PATH, "--config", config, snapshot_path, "--json", "--quiet"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout
        if not output:
            return {"findings": [], "severity_counts": {}}

        data = json.loads(output)
        findings = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for item in data.get("results", []):
            sev = item.get("extra", {}).get("severity", "WARNING").upper()
            sev_mapped = "high" if sev in ("ERROR", "HIGH", "CRITICAL") else "medium" if sev in ("WARNING", "MEDIUM") else "low"
            severity_counts[sev_mapped] += 1

            findings.append({
                "tool": "semgrep",
                "rule_id": item.get("check_id", ""),
                "file": item.get("path", ""),
                "line": item.get("start", {}).get("line", 0),
                "severity": sev_mapped.upper(),
                "message": item.get("extra", {}).get("message", ""),
                "snippet": item.get("extra", {}).get("lines", ""),
            })

        return {"findings": findings, "severity_counts": severity_counts}

    except FileNotFoundError:
        logger.warning("Semgrep not installed. Using fallback analysis.")
        return _semgrep_fallback_analysis(snapshot_path)
    except subprocess.TimeoutExpired:
        logger.warning("Semgrep scan timed out")
        return {"findings": [], "severity_counts": {}}
    except json.JSONDecodeError:
        logger.warning("Failed to parse Semgrep output")
        return {"findings": [], "severity_counts": {}}


def _bandit_fallback_analysis(snapshot_path: str) -> Dict:
    """Pattern-based fallback when Bandit is not installed."""
    findings = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    dangerous_patterns = {
        "eval(": ("HIGH", "Use of eval() is dangerous — potential code injection (B307)"),
        "exec(": ("HIGH", "Use of exec() is dangerous — potential code injection (B102)"),
        "subprocess.call(": ("MEDIUM", "Use of subprocess.call with potential shell injection (B603)"),
        "shell=True": ("HIGH", "subprocess call with shell=True is dangerous (B602)"),
        "pickle.loads": ("HIGH", "Deserialization of untrusted data via pickle (B301)"),
        "yaml.load(": ("MEDIUM", "Use of yaml.load without SafeLoader (B506)"),
        "md5": ("MEDIUM", "Use of weak hash function MD5 (B303)"),
        "password": ("LOW", "Possible hardcoded password (B105)"),
        "secret": ("LOW", "Possible hardcoded secret (B105)"),
        "assert ": ("LOW", "Use of assert in production code (B101)"),
    }

    snap = Path(snapshot_path)
    for fpath in snap.rglob("*.py"):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(content.splitlines(), 1):
                for pattern, (sev, msg) in dangerous_patterns.items():
                    if pattern in line:
                        severity_counts[sev.lower()] += 1
                        findings.append({
                            "tool": "bandit-fallback",
                            "file": str(fpath.relative_to(snap)),
                            "line": line_no,
                            "severity": sev,
                            "confidence": "MEDIUM",
                            "issue": msg,
                        })
        except Exception:
            continue

    return {"findings": findings, "severity_counts": severity_counts}


def _semgrep_fallback_analysis(snapshot_path: str) -> Dict:
    """Pattern-based fallback when Semgrep is not installed."""
    findings = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    patterns = {
        "cursor.execute(f\"": ("HIGH", "Potential SQL injection via f-string in query"),
        "cursor.execute(\"": ("MEDIUM", "Possible SQL injection via string concatenation"),
        "os.system(": ("HIGH", "OS command execution — potential command injection"),
        "innerHTML": ("MEDIUM", "Direct innerHTML assignment — potential XSS"),
        "dangerouslySetInnerHTML": ("MEDIUM", "React dangerouslySetInnerHTML — potential XSS"),
        "document.write": ("MEDIUM", "document.write — potential XSS vector"),
    }

    snap = Path(snapshot_path)
    for ext in ("*.py", "*.js", "*.ts", "*.jsx", "*.tsx"):
        for fpath in snap.rglob(ext):
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                for line_no, line in enumerate(content.splitlines(), 1):
                    for pattern, (sev, msg) in patterns.items():
                        if pattern in line:
                            severity_counts[sev.lower()] += 1
                            findings.append({
                                "tool": "semgrep-fallback",
                                "rule_id": "custom-pattern",
                                "file": str(fpath.relative_to(snap)),
                                "line": line_no,
                                "severity": sev,
                                "message": msg,
                            })
            except Exception:
                continue

    return {"findings": findings, "severity_counts": severity_counts}
