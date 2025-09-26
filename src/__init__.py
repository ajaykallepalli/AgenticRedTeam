"""
Agentic Red-Team Manager: Automated, Safe Adversarial Testing for Agentic Systems

A comprehensive framework for automated adversarial testing of agentic AI systems.
"""

__version__ = "0.1.0"
__author__ = "Agentic Red Team Contributors"
__email__ = "support@agenticredteam.com"

from .adversarial import RedTeamManager
from .scenarios import ScenarioLoader, ScenarioBuilder
from .evaluation import SafetyEvaluator
from .reporting import ReportGenerator

__all__ = [
    "RedTeamManager",
    "ScenarioLoader", 
    "ScenarioBuilder",
    "SafetyEvaluator",
    "ReportGenerator",
]