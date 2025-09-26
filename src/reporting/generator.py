"""
Report Generator

Main class for generating comprehensive test reports.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from .formats import HTMLReportFormatter, JSONReportFormatter, PDFReportFormatter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports from adversarial test results.
    
    Supports multiple output formats and customizable templates.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            config: Report generation configuration
        """
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'reports'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize formatters
        self.formatters = {
            'html': HTMLReportFormatter(config.get('html', {})),
            'json': JSONReportFormatter(config.get('json', {})),
            'pdf': PDFReportFormatter(config.get('pdf', {}))
        }
        
    def generate(self, results: List[Dict[str, Any]], 
                format: str = 'html', 
                output_path: Optional[str] = None) -> str:
        """
        Generate a comprehensive test report.
        
        Args:
            results: List of test results to include
            format: Output format ('html', 'json', 'pdf')
            output_path: Custom output path (optional)
            
        Returns:
            Path to generated report file
        """
        logger.info(f"Generating {format.upper()} report for {len(results)} test results")
        
        if format not in self.formatters:
            raise ValueError(f"Unsupported format: {format}")
        
        # Generate report filename if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"redteam_report_{timestamp}.{format}"
            output_path = str(self.output_dir / filename)
        
        # Prepare report data
        report_data = self._prepare_report_data(results)
        
        # Generate report using appropriate formatter
        formatter = self.formatters[format]
        formatter.generate(report_data, output_path)
        
        logger.info(f"Report generated: {output_path}")
        return output_path
    
    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of test results.
        
        Args:
            results: Test results to summarize
            
        Returns:
            Summary statistics and key findings
        """
        if not results:
            return {
                'total_tests': 0,
                'successful_attacks': 0,
                'vulnerabilities_found': 0,
                'average_safety_score': 0,
                'risk_distribution': {},
                'recommendations': []
            }
        
        # Calculate summary statistics
        total_tests = len(results)
        successful_attacks = sum(1 for r in results if r.get('success', False))
        vulnerabilities_found = sum(1 for r in results 
                                  if r.get('execution', {}).get('vulnerability_found', False))
        
        # Safety scores
        safety_scores = [r.get('safety', {}).get('overall_assessment', {}).get('safety_score', 0) 
                        for r in results]
        average_safety_score = sum(safety_scores) / len(safety_scores) if safety_scores else 0
        
        # Risk level distribution
        risk_levels = [r.get('safety', {}).get('overall_assessment', {}).get('risk_level', 'unknown') 
                      for r in results]
        risk_distribution = {}
        for risk_level in risk_levels:
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Collect all recommendations
        all_recommendations = []
        for result in results:
            recommendations = result.get('safety', {}).get('recommendations', [])
            all_recommendations.extend(recommendations)
        
        # Get unique recommendations with counts
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        top_recommendations = sorted(recommendation_counts.items(), 
                                   key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_tests': total_tests,
            'successful_attacks': successful_attacks,
            'vulnerabilities_found': vulnerabilities_found,
            'success_rate': successful_attacks / total_tests if total_tests > 0 else 0,
            'vulnerability_rate': vulnerabilities_found / total_tests if total_tests > 0 else 0,
            'average_safety_score': round(average_safety_score, 2),
            'min_safety_score': min(safety_scores) if safety_scores else 0,
            'max_safety_score': max(safety_scores) if safety_scores else 0,
            'risk_distribution': risk_distribution,
            'top_recommendations': [rec for rec, count in top_recommendations],
            'critical_findings': self._identify_critical_findings(results)
        }
    
    def _prepare_report_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare comprehensive report data structure."""
        
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'generator_version': '1.0.0',
                'total_results': len(results)
            },
            'executive_summary': self.generate_summary(results),
            'detailed_results': results,
            'analysis': {
                'scenario_breakdown': self._analyze_scenarios(results),
                'attack_vector_analysis': self._analyze_attack_vectors(results),
                'temporal_analysis': self._analyze_temporal_patterns(results),
                'risk_analysis': self._analyze_risk_patterns(results)
            },
            'recommendations': {
                'immediate_actions': self._get_immediate_actions(results),
                'short_term_improvements': self._get_short_term_improvements(results),
                'long_term_strategy': self._get_long_term_strategy(results)
            },
            'appendices': {
                'methodology': self._get_methodology_description(),
                'glossary': self._get_glossary(),
                'references': self._get_references()
            }
        }
        
        return report_data
    
    def _analyze_scenarios(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results by scenario categories."""
        scenario_stats = {}
        
        for result in results:
            scenario = result.get('scenario', {})
            category = scenario.get('category', 'unknown')
            
            if category not in scenario_stats:
                scenario_stats[category] = {
                    'count': 0,
                    'successful_attacks': 0,
                    'average_safety_score': 0,
                    'scenarios': []
                }
            
            stats = scenario_stats[category]
            stats['count'] += 1
            stats['scenarios'].append(scenario.get('name', 'Unknown'))
            
            if result.get('success', False):
                stats['successful_attacks'] += 1
            
            safety_score = result.get('safety', {}).get('overall_assessment', {}).get('safety_score', 0)
            stats['average_safety_score'] += safety_score
        
        # Calculate averages
        for category, stats in scenario_stats.items():
            if stats['count'] > 0:
                stats['average_safety_score'] = stats['average_safety_score'] / stats['count']
                stats['success_rate'] = stats['successful_attacks'] / stats['count']
        
        return scenario_stats
    
    def _analyze_attack_vectors(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze effectiveness of different attack vectors."""
        vector_analysis = {}
        
        for result in results:
            execution = result.get('execution', {})
            iterations = execution.get('iterations', [])
            
            for iteration in iterations:
                attack_vector = iteration.get('attack_vector', {})
                vector_type = attack_vector.get('type', 'unknown')
                
                if vector_type not in vector_analysis:
                    vector_analysis[vector_type] = {
                        'total_attempts': 0,
                        'successful_attempts': 0,
                        'average_risk_score': 0,
                        'risk_scores': []
                    }
                
                stats = vector_analysis[vector_type]
                stats['total_attempts'] += 1
                
                if iteration.get('vulnerability_detected', False):
                    stats['successful_attempts'] += 1
                
                risk_score = iteration.get('vulnerability_details', {}).get('risk_score', 0)
                stats['risk_scores'].append(risk_score)
        
        # Calculate statistics
        for vector_type, stats in vector_analysis.items():
            if stats['risk_scores']:
                stats['average_risk_score'] = sum(stats['risk_scores']) / len(stats['risk_scores'])
                stats['max_risk_score'] = max(stats['risk_scores'])
            
            if stats['total_attempts'] > 0:
                stats['success_rate'] = stats['successful_attempts'] / stats['total_attempts']
        
        return vector_analysis
    
    def _analyze_temporal_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in test results."""
        # Simple temporal analysis - could be expanded
        execution_times = []
        timestamps = []
        
        for result in results:
            timestamp = result.get('timestamp')
            if timestamp:
                timestamps.append(timestamp)
            
            execution = result.get('execution', {})
            duration = execution.get('duration', 0)
            if duration:
                execution_times.append(duration)
        
        return {
            'total_execution_time': sum(execution_times),
            'average_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
            'min_execution_time': min(execution_times) if execution_times else 0,
            'max_execution_time': max(execution_times) if execution_times else 0,
            'test_duration_distribution': self._categorize_durations(execution_times)
        }
    
    def _analyze_risk_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze risk patterns across all tests."""
        risk_factors = {}
        risk_scores = []
        
        for result in results:
            safety = result.get('safety', {})
            risk_assessment = safety.get('risk_assessment', {})
            
            # Collect risk factors
            factors = risk_assessment.get('risk_factors', [])
            for factor in factors:
                risk_factors[factor] = risk_factors.get(factor, 0) + 1
            
            # Collect risk scores
            risk_score = risk_assessment.get('risk_score', 0)
            risk_scores.append(risk_score)
        
        return {
            'common_risk_factors': sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)[:10],
            'average_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            'risk_score_distribution': self._categorize_risk_scores(risk_scores)
        }
    
    def _identify_critical_findings(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify critical findings requiring immediate attention."""
        critical_findings = []
        
        for result in results:
            safety = result.get('safety', {})
            overall_assessment = safety.get('overall_assessment', {})
            
            # Check for critical risk level
            if overall_assessment.get('risk_level') == 'critical':
                critical_findings.append({
                    'type': 'critical_risk',
                    'scenario': result.get('scenario', {}).get('name', 'Unknown'),
                    'description': 'Critical risk level detected',
                    'safety_score': overall_assessment.get('safety_score', 0)
                })
            
            # Check for very low safety scores
            safety_score = overall_assessment.get('safety_score', 100)
            if safety_score < 30:
                critical_findings.append({
                    'type': 'low_safety_score',
                    'scenario': result.get('scenario', {}).get('name', 'Unknown'),
                    'description': f'Very low safety score: {safety_score}/100',
                    'safety_score': safety_score
                })
            
            # Check for intervention requirements
            if overall_assessment.get('intervention_needed', False):
                critical_findings.append({
                    'type': 'intervention_needed',
                    'scenario': result.get('scenario', {}).get('name', 'Unknown'),
                    'description': 'Immediate intervention required',
                    'safety_score': safety_score
                })
        
        return critical_findings
    
    def _get_immediate_actions(self, results: List[Dict[str, Any]]) -> List[str]:
        """Get list of immediate actions required."""
        actions = set()
        
        for result in results:
            safety = result.get('safety', {})
            if safety.get('overall_assessment', {}).get('intervention_needed', False):
                actions.add("Immediate security review required")
            
            risk_level = safety.get('overall_assessment', {}).get('risk_level')
            if risk_level == 'critical':
                actions.add("Emergency security patch deployment")
            elif risk_level == 'high':
                actions.add("Priority security updates required")
        
        return list(actions)
    
    def _get_short_term_improvements(self, results: List[Dict[str, Any]]) -> List[str]:
        """Get short-term improvement recommendations."""
        return [
            "Implement enhanced input validation",
            "Strengthen prompt engineering guidelines",
            "Deploy additional monitoring systems",
            "Conduct security awareness training"
        ]
    
    def _get_long_term_strategy(self, results: List[Dict[str, Any]]) -> List[str]:
        """Get long-term strategic recommendations."""
        return [
            "Develop comprehensive AI safety framework",
            "Establish regular red team testing schedule",
            "Build automated security monitoring pipeline",
            "Create incident response playbooks"
        ]
    
    def _categorize_durations(self, execution_times: List[float]) -> Dict[str, int]:
        """Categorize execution times into buckets."""
        categories = {'<30s': 0, '30s-2m': 0, '2m-5m': 0, '>5m': 0}
        
        for duration in execution_times:
            if duration < 30:
                categories['<30s'] += 1
            elif duration < 120:
                categories['30s-2m'] += 1
            elif duration < 300:
                categories['2m-5m'] += 1
            else:
                categories['>5m'] += 1
        
        return categories
    
    def _categorize_risk_scores(self, risk_scores: List[float]) -> Dict[str, int]:
        """Categorize risk scores into ranges."""
        categories = {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0}
        
        for score in risk_scores:
            if score <= 25:
                categories['0-25'] += 1
            elif score <= 50:
                categories['26-50'] += 1
            elif score <= 75:
                categories['51-75'] += 1
            else:
                categories['76-100'] += 1
        
        return categories
    
    def _get_methodology_description(self) -> str:
        """Get methodology description for appendix."""
        return """
        This report was generated using the Agentic Red-Team Manager framework.
        
        The testing methodology involves:
        1. Scenario-based adversarial testing
        2. Automated attack vector execution
        3. Multi-dimensional safety evaluation
        4. Risk assessment and scoring
        5. Comprehensive reporting and recommendations
        """
    
    def _get_glossary(self) -> Dict[str, str]:
        """Get glossary of terms."""
        return {
            'Attack Vector': 'A specific method or technique used to exploit vulnerabilities',
            'Safety Score': 'Numerical assessment of system safety (0-100, higher is better)',
            'Risk Level': 'Categorical assessment of potential risk (low, medium, high, critical)',
            'Vulnerability Rate': 'Percentage of tests that detected vulnerabilities',
            'Jailbreak': 'Technique to bypass AI safety restrictions',
            'Prompt Injection': 'Attack that manipulates AI through crafted input prompts'
        }
    
    def _get_references(self) -> List[str]:
        """Get list of references."""
        return [
            "OWASP AI Security and Privacy Guide",
            "NIST AI Risk Management Framework",
            "Adversarial Machine Learning: A Taxonomy and Terminology",
            "Red Teaming Language Models with Language Models"
        ]