from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models import BugReport, CodeSnapshot, AnalysisResult, Project
from backend.core import github_service, scoring_service
from backend.core.prompts import build_rca_prompt, SYSTEM_PROMPT
from backend.config import get_settings
from backend.services.ai_analysis_service import OllamaService
import json
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
ai_analysis_service = OllamaService(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    timeout=settings.OLLAMA_TIMEOUT
)


class AnalysisService:
    """Service for bug analysis pipeline."""

    @staticmethod
    async def create_and_analyze_report(
        session: AsyncSession, bug_report: BugReport, project: Project
    ) -> AnalysisResult | None:
        """
        Execute full analysis pipeline:
        1. Fetch code from GitHub
        2. Extract code context
        3. Create snapshot
        4. Run AI analysis
        5. Compute score
        6. Store results
        """
        try:
            # Step 1: Fetch code context from GitHub
            logger.info(f"Fetching code context for {bug_report.affected_file}")
            code_context = await github_service.extract_code_context(
                repo_url=project.repository_url,
                file_path=bug_report.affected_file,
                affected_line=bug_report.affected_line,
                context_lines=10,
            )

            if not code_context:
                logger.error(f"Failed to fetch code context for {bug_report.affected_file}")
                return None

            # Step 2: Create code snapshot
            logger.info(f"Creating code snapshot")
            snapshot_data = {
                "file_path": code_context.get("file_path"),
                "affected_line": code_context.get("affected_line"),
                "context_code": code_context.get("context_code"),
                "total_lines": code_context.get("total_lines"),
            }

            code_snapshot = CodeSnapshot(
                bug_report_id=bug_report.id,
                repo_url=project.repository_url,
                commit_hash=None,
                snapshot_data=json.dumps(snapshot_data),
            )
            session.add(code_snapshot)
            await session.flush()

            # Step 3: Enrich knowledge (mock)
            enriched_knowledge = {
                "vulnerability_type": "Code Injection" if "injection" in bug_report.description.lower() else "Other",
                "cwe_references": [
                    "CWE-89 (SQL Injection)",
                    "CWE-94 (Code Injection)",
                ],
                "common_patterns": [
                    "Unsanitized user input",
                    "Dynamic query construction",
                ],
            }

            # Step 4: Run AI analysis
            logger.info(f"Running AI analysis")
            analysis_result_obj = await ai_analysis_service.analyze_repo(
                repo_url=project.repository_url
            )
            
            ai_result = {
                "root_cause": getattr(analysis_result_obj, "root_cause", ""),
                "exploit_payload": getattr(analysis_result_obj, "proof_of_concept", ""),
                "suggested_patch": getattr(analysis_result_obj, "recommended_fix", ""),
                "confidence_score": getattr(analysis_result_obj, "cvss_score", 0.5),
            }

            # Step 5: Compute score
            logger.info(f"Computing severity score")
            confidence = ai_result.get("confidence_score", 0.5)
            score = scoring_service.compute_score(
                confidence_score=confidence,
                severity=bug_report.severity,
                affected_lines=1,
            )

            # Step 6: Store analysis result
            logger.info(f"Storing analysis result")
            analysis_result = AnalysisResult(
                bug_report_id=bug_report.id,
                root_cause=ai_result.get("root_cause"),
                exploit_payload=ai_result.get("exploit_payload"),
                suggested_patch=ai_result.get("suggested_patch"),
                confidence_score=score,
            )
            session.add(analysis_result)
            await session.commit()
            await session.refresh(analysis_result)

            logger.info(f"Analysis complete for bug report {bug_report.id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Analysis pipeline error: {str(e)}")
            await session.rollback()
            return None

    @staticmethod
    async def get_analysis_result(
        session: AsyncSession, bug_report_id
    ) -> AnalysisResult | None:
        """Get analysis result for bug report."""
        result = await session.execute(
            select(AnalysisResult).where(AnalysisResult.bug_report_id == bug_report_id)
        )
        return result.scalars().first()
