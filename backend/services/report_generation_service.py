"""
Report Generation Service
Generates PDF, HTML, and JSON reports of vulnerability analysis
"""

import logging
import json
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed, PDF generation will use fallback")


class ReportGenerationService:
    """Service for generating vulnerability analysis reports"""

    def __init__(self, reports_dir: Optional[str] = None):
        self.reports_dir = Path(reports_dir or "./reports")
        self.reports_dir.mkdir(exist_ok=True)

    async def generate_report(
        self,
        analysis_result_id: UUID,
        analysis_data: Dict,
        exploit_results: Dict,
        score_data: Dict,
        format: str = "pdf"
    ) -> str:
        """
        Generate comprehensive vulnerability report

        Args:
            analysis_result_id: ID of the analysis
            analysis_data: Root cause analysis data
            exploit_results: Exploit execution results
            score_data: Vulnerability score data
            format: Report format (pdf, html, json)

        Returns:
            Path to generated report file
        """
        if format == "pdf":
            return await self._generate_pdf_report(
                analysis_result_id, analysis_data, exploit_results, score_data
            )
        elif format == "html":
            return await self._generate_html_report(
                analysis_result_id, analysis_data, exploit_results, score_data
            )
        elif format == "json":
            return await self._generate_json_report(
                analysis_result_id, analysis_data, exploit_results, score_data
            )
        else:
            raise ValueError(f"Unsupported report format: {format}")

    async def _generate_pdf_report(
        self,
        analysis_id: UUID,
        analysis_data: Dict,
        exploit_results: Dict,
        score_data: Dict
    ) -> str:
        """Generate PDF report using ReportLab"""

        if not HAS_REPORTLAB:
            logger.warning("ReportLab not available, generating HTML instead")
            return await self._generate_html_report(
                analysis_id, analysis_data, exploit_results, score_data
            )

        filename = f"report_{analysis_id}.pdf"
        filepath = self.reports_dir / filename

        try:
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#E8001D'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            story.append(Paragraph("🛡️ Zorix Vulnerability Report", title_style))
            story.append(Spacer(1, 0.3 * inch))

            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            summary_text = f"""
            <b>Vulnerability Type:</b> {analysis_data.get('vulnerability_type', 'Unknown')}<br/>
            <b>Severity Level:</b> <font color="red">{score_data.get('severity', 'UNKNOWN')}</font><br/>
            <b>CVSS Score:</b> <b>{score_data.get('cvss_score', 0.0)}/10.0</b><br/>
            <b>Confidence:</b> {score_data.get('confidence', 0.0)*100:.1f}%<br/>
            <b>Report Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))

            # Root Cause Analysis
            story.append(Paragraph("Root Cause Analysis", styles['Heading2']))
            root_cause = analysis_data.get('root_cause', 'Analysis pending...')
            story.append(Paragraph(root_cause, styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))

            # Exploit Results
            story.append(Paragraph("Exploit Execution Results", styles['Heading2']))
            
            exploit_summary = f"""
            <b>Total Exploits Tested:</b> {exploit_results.get('total_exploits_tested', 0)}<br/>
            <b>Vulnerabilities Confirmed:</b> {exploit_results.get('vulnerabilities_confirmed', 0)}<br/>
            <b>Success Rate:</b> {exploit_results.get('success_rate', 0)*100:.1f}%
            """
            story.append(Paragraph(exploit_summary, styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))

            # Recommendations
            story.append(Paragraph("Recommendations", styles['Heading2']))
            recommendations = analysis_data.get('recommended_fix', 'No recommendations available')
            story.append(Paragraph(recommendations, styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))

            # Technical Details
            story.append(PageBreak())
            story.append(Paragraph("Technical Details", styles['Heading2']))
            
            attack_vector = analysis_data.get('attack_vector', 'N/A')
            poc = analysis_data.get('proof_of_concept', 'N/A')
            
            technical = f"""
            <b>Attack Vector:</b><br/>
            {attack_vector}<br/><br/>
            <b>Proof of Concept:</b><br/>
            <font face="Courier" size="9">{poc}</font>
            """
            story.append(Paragraph(technical, styles['Normal']))

            # Build PDF
            doc.build(story)
            logger.info(f"PDF report generated: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            # Fallback to HTML
            return await self._generate_html_report(
                analysis_id, analysis_data, exploit_results, score_data
            )

    async def _generate_html_report(
        self,
        analysis_id: UUID,
        analysis_data: Dict,
        exploit_results: Dict,
        score_data: Dict
    ) -> str:
        """Generate HTML report"""

        filename = f"report_{analysis_id}.html"
        filepath = self.reports_dir / filename

        severity = score_data.get('severity', 'UNKNOWN')
        color_map = {
            'CRITICAL': '#ff0000',
            'HIGH': '#ff6600',
            'MEDIUM': '#ffcc00',
            'LOW': '#00cc00',
            'INFO': '#0099ff'
        }
        color = color_map.get(severity, '#cccccc')

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zorix Vulnerability Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            color: #e0e0e0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: rgba(20, 20, 20, 0.95);
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }}
        .header {{
            border-bottom: 2px solid rgba(232, 0, 29, 0.3);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 32px;
            font-weight: bold;
            color: #e8001d;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #999;
            font-size: 14px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: bold;
            color: #e8001d;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(232, 0, 29, 0.2);
        }}
        .severity-badge {{
            display: inline-block;
            background: {color};
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .score {{
            font-size: 48px;
            font-weight: bold;
            color: {color};
            text-align: center;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background: rgba(232, 0, 29, 0.05);
            border-left: 3px solid {color};
            padding: 15px;
            border-radius: 4px;
        }}
        .info-card strong {{
            color: #e8001d;
        }}
        .code-block {{
            background: rgba(0, 0, 0, 0.3);
            border-left: 3px solid #e8001d;
            padding: 15px;
            margin: 15px 0;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #00ff00;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(232, 0, 29, 0.2);
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🛡️ Zorix Security Report</div>
            <div class="subtitle">Vulnerability Analysis & Exploit Validation</div>
        </div>

        <div class="section">
            <div class="section-title">Severity Assessment</div>
            <div style="text-align: center;">
                <div class="severity-badge">{severity}</div>
            </div>
            <div class="score">{score_data.get('cvss_score', 0.0)}/10.0</div>
            <div class="info-grid">
                <div class="info-card">
                    <strong>CVSS Vector:</strong><br/>
                    {score_data.get('cvss_vector', 'N/A')}
                </div>
                <div class="info-card">
                    <strong>Exploitability:</strong><br/>
                    {score_data.get('exploitability', 0.0)*100:.1f}%
                </div>
                <div class="info-card">
                    <strong>Impact:</strong><br/>
                    {score_data.get('impact_score', 0.0)*100:.1f}%
                </div>
                <div class="info-card">
                    <strong>Confidence:</strong><br/>
                    {score_data.get('confidence', 0.0)*100:.1f}%
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Vulnerability Type</div>
            <p><strong>{analysis_data.get('vulnerability_type', 'Unknown')}</strong></p>
        </div>

        <div class="section">
            <div class="section-title">Root Cause Analysis</div>
            <p>{analysis_data.get('root_cause', 'Analysis pending...')}</p>
        </div>

        <div class="section">
            <div class="section-title">Attack Vector</div>
            <p>{analysis_data.get('attack_vector', 'N/A')}</p>
        </div>

        <div class="section">
            <div class="section-title">Proof of Concept</div>
            <div class="code-block">{analysis_data.get('proof_of_concept', 'N/A')}</div>
        </div>

        <div class="section">
            <div class="section-title">Exploit Validation Results</div>
            <div class="info-grid">
                <div class="info-card">
                    <strong>Total Exploits Tested:</strong><br/>
                    {exploit_results.get('total_exploits_tested', 0)}
                </div>
                <div class="info-card">
                    <strong>Confirmed Vulnerabilities:</strong><br/>
                    {exploit_results.get('vulnerabilities_confirmed', 0)}
                </div>
                <div class="info-card">
                    <strong>Success Rate:</strong><br/>
                    {exploit_results.get('success_rate', 0)*100:.1f}%
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Recommendations</div>
            <p>{analysis_data.get('recommended_fix', 'No recommendations available')}</p>
        </div>

        <div class="footer">
            <p>Generated by Zorix Security Platform</p>
            <p>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
    </div>
</body>
</html>
        """

        try:
            filepath.write_text(html_content)
            logger.info(f"HTML report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise

    async def _generate_json_report(
        self,
        analysis_id: UUID,
        analysis_data: Dict,
        exploit_results: Dict,
        score_data: Dict
    ) -> str:
        """Generate JSON report"""

        filename = f"report_{analysis_id}.json"
        filepath = self.reports_dir / filename

        report_data = {
            "analysis_id": str(analysis_id),
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "vulnerability_type": analysis_data.get('vulnerability_type'),
                "severity": score_data.get('severity'),
                "cvss_score": score_data.get('cvss_score'),
                "confirmed": exploit_results.get('vulnerabilities_confirmed', 0) > 0,
            },
            "analysis": analysis_data,
            "exploit_results": exploit_results,
            "score": score_data,
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            logger.info(f"JSON report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise
