"""
Red Team Manager - Main orchestration class for adversarial testing
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

from ..scenarios import Scenario
from ..sandbox import SandboxManager
from ..evaluation import SafetyEvaluator
from ..reporting import ReportGenerator
from .executor import TestExecutor

logger = logging.getLogger(__name__)


class RedTeamManager:
    """
    Main orchestration class for automated adversarial testing.
    
    Coordinates between scenario loading, test execution, safety evaluation,
    and report generation to provide comprehensive adversarial testing.
    """
    
    def __init__(self, config_file: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the Red Team Manager.
        
        Args:
            config_file: Path to YAML configuration file
            config: Configuration dictionary (overrides config_file)
        """
        self.config = self._load_config(config_file, config)
        
        # Initialize core components
        self.sandbox_manager = SandboxManager(self.config.get('sandbox', {}))
        self.safety_evaluator = SafetyEvaluator(self.config.get('safety', {}))
        self.report_generator = ReportGenerator(self.config.get('reporting', {}))
        self.test_executor = TestExecutor(self.config.get('executor', {}))
        
        logger.info("Red Team Manager initialized successfully")
    
    def execute_test(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Execute an adversarial test scenario.
        
        Args:
            scenario: The test scenario to execute
            
        Returns:
            Dictionary containing test results and metadata
        """
        logger.info(f"Executing test scenario: {scenario.name}")
        
        try:
            # Create isolated sandbox environment
            with self.sandbox_manager.create_environment(scenario.constraints) as env:
                # Execute the adversarial test
                raw_results = self.test_executor.run(scenario, env)
                
                # Evaluate safety and risk
                safety_results = self.safety_evaluator.evaluate(raw_results, scenario)
                
                # Combine results
                results = {
                    'scenario': scenario.to_dict(),
                    'execution': raw_results,
                    'safety': safety_results,
                    'timestamp': self._get_timestamp(),
                    'success': raw_results.get('success', False)
                }
                
                logger.info(f"Test completed. Safety score: {safety_results.get('score', 0)}")
                return results
                
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            raise
    
    def execute_test_suite(self, scenarios: List[Scenario]) -> List[Dict[str, Any]]:
        """
        Execute multiple test scenarios.
        
        Args:
            scenarios: List of scenarios to execute
            
        Returns:
            List of test results
        """
        results = []
        for scenario in scenarios:
            try:
                result = self.execute_test(scenario)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to execute scenario {scenario.name}: {str(e)}")
                results.append({
                    'scenario': scenario.to_dict(),
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]], format: str = 'html') -> str:
        """
        Generate a comprehensive test report.
        
        Args:
            results: Test results to include in report
            format: Report format ('html', 'pdf', 'json')
            
        Returns:
            Path to generated report file
        """
        return self.report_generator.generate(results, format)
    
    def _load_config(self, config_file: Optional[str], config: Optional[Dict]) -> Dict:
        """Load configuration from file or dictionary."""
        if config:
            return config
            
        if config_file:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            'sandbox': {'timeout': 300, 'memory_limit': '1GB'},
            'safety': {'max_risk_level': 'medium'},
            'reporting': {'output_dir': 'reports'},
            'executor': {'parallel_jobs': 1}
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()