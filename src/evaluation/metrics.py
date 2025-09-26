"""
Safety Metrics and Risk Assessment Data Models
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class SafetyMetrics:
    """
    Comprehensive safety metrics for adversarial test results.
    """
    total_iterations: int = 0
    successful_attacks: int = 0
    vulnerability_rate: float = 0.0
    harmful_response_rate: float = 0.0
    average_risk_score: float = 0.0
    max_risk_score: float = 0.0
    response_consistency: float = 1.0
    attack_success_by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary representation."""
        return {
            'total_iterations': self.total_iterations,
            'successful_attacks': self.successful_attacks,
            'vulnerability_rate': self.vulnerability_rate,
            'harmful_response_rate': self.harmful_response_rate,
            'average_risk_score': self.average_risk_score,
            'max_risk_score': self.max_risk_score,
            'response_consistency': self.response_consistency,
            'attack_success_by_type': self.attack_success_by_type
        }


@dataclass
class RiskAssessment:
    """
    Comprehensive risk assessment results.
    """
    overall_risk_level: str = "low"  # low, medium, high, critical
    risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    vulnerability_categories: List[str] = field(default_factory=list)
    impact_assessment: str = "low"  # low, medium, high
    likelihood_assessment: str = "low"  # low, medium, high
    mitigation_urgency: str = "low"  # low, moderate, urgent, immediate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary representation."""
        return {
            'overall_risk_level': self.overall_risk_level,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors,
            'vulnerability_categories': self.vulnerability_categories,
            'impact_assessment': self.impact_assessment,
            'likelihood_assessment': self.likelihood_assessment,
            'mitigation_urgency': self.mitigation_urgency
        }