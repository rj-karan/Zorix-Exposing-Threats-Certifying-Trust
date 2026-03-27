"""
Patch Retrieval Service
Queries NVD API and local knowledge base for CVE/patch information.
"""

import logging
import json
from typing import Dict, Optional, List
from datetime import datetime

import httpx

from backend.config import get_settings
from backend.core.logger import pipeline_logger

logger = logging.getLogger(__name__)
settings = get_settings()


async def retrieve_patch_info(
    cwe_id: Optional[str] = None,
    root_cause: Optional[Dict] = None,
    vulnerability_type: Optional[str] = None,
    analysis_id=None,
) -> Dict:
    """
    Retrieve patch intelligence from NVD API and local knowledge.

    Args:
        cwe_id: CWE identifier (e.g., "CWE-89")
        root_cause: Root cause analysis dict
        vulnerability_type: Type of vulnerability
        analysis_id: For logging context

    Returns:
        { cve_ids, cvss_score, patch_description, references, patches_available }
    """
    pipeline_logger.info(
        f"Retrieving patch info for CWE={cwe_id}, type={vulnerability_type}",
        stage="PATCHING",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    result = {
        "cve_ids": [],
        "cvss_score": 0.0,
        "patch_description": "",
        "references": [],
        "patches_available": False,
        "advisories": [],
    }

    # Query NVD API
    try:
        nvd_data = await _query_nvd(cwe_id, vulnerability_type)
        if nvd_data:
            result.update(nvd_data)
    except Exception as e:
        logger.warning(f"NVD API query failed: {e}")

    # Enrich with local knowledge base
    local_data = _get_local_patch_knowledge(cwe_id, vulnerability_type)
    if local_data:
        if not result["patch_description"]:
            result["patch_description"] = local_data.get("patch_description", "")
        result["references"].extend(local_data.get("references", []))
        if not result["patches_available"] and local_data.get("patches_available"):
            result["patches_available"] = True

    pipeline_logger.info(
        f"Found {len(result['cve_ids'])} CVEs, patches_available={result['patches_available']}",
        stage="PATCHING",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    return result


async def _query_nvd(
    cwe_id: Optional[str], vulnerability_type: Optional[str]
) -> Optional[Dict]:
    """Query NVD API for CVE data related to the vulnerability."""
    if not cwe_id and not vulnerability_type:
        return None

    params = {}
    if cwe_id:
        # NVD API uses cweId as a filter
        params["cweId"] = cwe_id.upper() if cwe_id.startswith("CWE") else f"CWE-{cwe_id}"
    if vulnerability_type:
        params["keywordSearch"] = vulnerability_type.replace("_", " ")

    params["resultsPerPage"] = 5

    headers = {}
    if settings.NVD_API_KEY:
        headers["apiKey"] = settings.NVD_API_KEY

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                settings.NVD_API_URL,
                params=params,
                headers=headers,
            )

            if resp.status_code == 403:
                logger.warning("NVD API rate limited")
                return None

            if resp.status_code != 200:
                logger.warning(f"NVD API returned {resp.status_code}")
                return None

            data = resp.json()
            vulnerabilities = data.get("vulnerabilities", [])

            if not vulnerabilities:
                return None

            cve_ids = []
            max_cvss = 0.0
            references = []
            descriptions = []

            for vuln in vulnerabilities[:5]:
                cve = vuln.get("cve", {})
                cve_id = cve.get("id", "")
                if cve_id:
                    cve_ids.append(cve_id)

                # Extract CVSS score
                metrics = cve.get("metrics", {})
                for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                    items = metrics.get(version, [])
                    if items:
                        score = items[0].get("cvssData", {}).get("baseScore", 0.0)
                        max_cvss = max(max_cvss, score)
                        break

                # Extract references
                for ref in cve.get("references", [])[:3]:
                    url = ref.get("url", "")
                    if url:
                        references.append(url)

                # Extract description
                for desc in cve.get("descriptions", []):
                    if desc.get("lang") == "en":
                        descriptions.append(desc.get("value", ""))
                        break

            return {
                "cve_ids": cve_ids,
                "cvss_score": max_cvss,
                "patch_description": "; ".join(descriptions[:2]) if descriptions else "",
                "references": references[:10],
                "patches_available": len(cve_ids) > 0,
            }

    except httpx.TimeoutException:
        logger.warning("NVD API request timed out")
        return None
    except Exception as e:
        logger.warning(f"NVD API error: {e}")
        return None


def _get_local_patch_knowledge(
    cwe_id: Optional[str], vulnerability_type: Optional[str]
) -> Optional[Dict]:
    """Get patch recommendations from local knowledge base."""
    knowledge = {
        "CWE-89": {
            "patch_description": "Use parameterized queries or prepared statements instead of string concatenation. Use ORM frameworks that handle escaping automatically.",
            "references": [
                "https://cwe.mitre.org/data/definitions/89.html",
                "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
            ],
            "patches_available": True,
        },
        "CWE-79": {
            "patch_description": "Implement context-aware output encoding. Use Content Security Policy headers. Sanitize user input with libraries like DOMPurify or bleach.",
            "references": [
                "https://cwe.mitre.org/data/definitions/79.html",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
            ],
            "patches_available": True,
        },
        "CWE-78": {
            "patch_description": "Avoid shell commands. Use language-native libraries. If shell is required, use allowlist validation and never pass user input directly.",
            "references": [
                "https://cwe.mitre.org/data/definitions/78.html",
                "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html",
            ],
            "patches_available": True,
        },
        "CWE-22": {
            "patch_description": "Validate and canonicalize file paths. Use allowlist of permitted directories. Never concatenate user input into file paths directly.",
            "references": [
                "https://cwe.mitre.org/data/definitions/22.html",
            ],
            "patches_available": True,
        },
    }

    # Map vulnerability types to CWE IDs
    type_to_cwe = {
        "SQL_INJECTION": "CWE-89",
        "XSS": "CWE-79",
        "COMMAND_INJECTION": "CWE-78",
        "PATH_TRAVERSAL": "CWE-22",
        "CSRF": "CWE-352",
        "XXE": "CWE-611",
    }

    lookup_cwe = cwe_id
    if not lookup_cwe and vulnerability_type:
        lookup_cwe = type_to_cwe.get(vulnerability_type.upper())

    if lookup_cwe and lookup_cwe in knowledge:
        return knowledge[lookup_cwe]

    return None
