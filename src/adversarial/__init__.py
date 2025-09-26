"""
Adversarial Testing Framework

Core module for automated adversarial testing of agentic AI systems.
"""

from .manager import RedTeamManager
from .attacks import AttackVector, AttackRegistry
from .executor import TestExecutor

__all__ = ["RedTeamManager", "AttackVector", "AttackRegistry", "TestExecutor"]