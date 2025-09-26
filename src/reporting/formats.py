"""
Report Format Implementations
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ReportFormatter(ABC):
    """Base class for report formatters."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate report in specific format."""
        pass


class JSONReportFormatter(ReportFormatter):
    """JSON report formatter."""
    
    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate JSON report."""
        logger.info(f"Generating JSON report: {output_path}")
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)


class HTMLReportFormatter(ReportFormatter):
    """HTML report formatter."""
    
    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate HTML report."""
        logger.info(f"Generating HTML report: {output_path}")
        
        html_template = self._get_html_template()
        html_content = html_template.format(
            title="Agentic Red-Team Report",
            summary=self._format_summary(data.get('executive_summary', {})),
            details=self._format_details(data.get('detailed_results', [])),
            analysis=self._format_analysis(data.get('analysis', {}))
        )
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _get_html_template(self) -> str:
        """Get basic HTML template."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #e9ecef; border-radius: 5px; }}
        .details {{ margin: 20px 0; }}
        .test-result {{ margin: 10px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }}
        .risk-critical {{ border-left-color: #dc3545; }}
        .risk-high {{ border-left-color: #fd7e14; }}
        .risk-medium {{ border-left-color: #ffc107; }}
        .risk-low {{ border-left-color: #28a745; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Generated: {{timestamp}}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        {summary}
    </div>
    
    <div class="details">
        <h2>Test Results</h2>
        {details}
    </div>
    
    <div class="analysis">
        <h2>Analysis</h2>
        {analysis}
    </div>
</body>
</html>
        """
    
    def _format_summary(self, summary: Dict[str, Any]) -> str:
        """Format executive summary section."""
        return f"""
        <div class="metric">
            <strong>Total Tests:</strong> {summary.get('total_tests', 0)}
        </div>
        <div class="metric">
            <strong>Successful Attacks:</strong> {summary.get('successful_attacks', 0)}
        </div>
        <div class="metric">
            <strong>Average Safety Score:</strong> {summary.get('average_safety_score', 0)}/100
        </div>
        <div class="metric">
            <strong>Vulnerability Rate:</strong> {summary.get('vulnerability_rate', 0)*100:.1f}%
        </div>
        """
    
    def _format_details(self, results: list) -> str:
        """Format detailed results section."""
        html = ""
        for result in results[:10]:  # Limit to first 10 results
            scenario = result.get('scenario', {})
            safety = result.get('safety', {})
            assessment = safety.get('overall_assessment', {})
            risk_level = assessment.get('risk_level', 'low')
            
            html += f"""
            <div class="test-result risk-{risk_level}">
                <h3>{scenario.get('name', 'Unknown Scenario')}</h3>
                <p><strong>Category:</strong> {scenario.get('category', 'unknown')}</p>
                <p><strong>Risk Level:</strong> {risk_level}</p>
                <p><strong>Safety Score:</strong> {assessment.get('safety_score', 0)}/100</p>
                <p><strong>Success:</strong> {'Yes' if result.get('success', False) else 'No'}</p>
            </div>
            """
        
        return html
    
    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format analysis section."""
        return f"""
        <h3>Scenario Breakdown</h3>
        <pre>{json.dumps(analysis.get('scenario_breakdown', {}), indent=2)}</pre>
        
        <h3>Risk Analysis</h3>
        <pre>{json.dumps(analysis.get('risk_analysis', {}), indent=2)}</pre>
        """


class PDFReportFormatter(ReportFormatter):
    """PDF report formatter (placeholder)."""
    
    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate PDF report (placeholder implementation)."""
        logger.warning("PDF generation not yet implemented, generating JSON instead")
        
        # Fallback to JSON for now
        json_path = output_path.replace('.pdf', '.json')
        JSONReportFormatter(self.config).generate(data, json_path)