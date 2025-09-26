"""
Sandbox Manager - Orchestrates sandbox environments
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from .environment import SandboxEnvironment
from .docker_sandbox import DockerSandbox

logger = logging.getLogger(__name__)


class SandboxManager:
    """
    Manages creation and lifecycle of sandbox environments.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the sandbox manager.
        
        Args:
            config: Sandbox configuration
        """
        self.config = config
        self.default_timeout = config.get('timeout', 300)
        self.memory_limit = config.get('memory_limit', '1GB')
        self.network_isolation = config.get('network_isolation', True)
        self.active_environments: List[SandboxEnvironment] = []
        
        # Initialize Docker client if available
        try:
            import docker
            self.docker_client = docker.from_env()
            self.docker_available = True
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.docker_client = None
            self.docker_available = False
    
    @contextmanager
    def create_environment(self, constraints: Optional[Dict[str, Any]] = None):
        """
        Create a new sandbox environment with the given constraints.
        
        Args:
            constraints: Environment constraints and limits
            
        Yields:
            SandboxEnvironment: The created sandbox environment
        """
        environment = None
        try:
            if self.docker_available:
                environment = self._create_docker_environment(constraints or {})
            else:
                environment = self._create_mock_environment(constraints or {})
            
            self.active_environments.append(environment)
            logger.info(f"Created sandbox environment: {environment.id}")
            
            yield environment
            
        finally:
            if environment:
                self._cleanup_environment(environment)
    
    def _create_docker_environment(self, constraints: Dict[str, Any]) -> SandboxEnvironment:
        """Create a Docker-based sandbox environment."""
        return DockerSandbox(
            docker_client=self.docker_client,
            timeout=constraints.get('timeout', self.default_timeout),
            memory_limit=constraints.get('memory_limit', self.memory_limit),
            network_isolation=constraints.get('network_isolation', self.network_isolation),
            allowed_domains=constraints.get('allowed_domains', [])
        )
    
    def _create_mock_environment(self, constraints: Dict[str, Any]) -> SandboxEnvironment:
        """Create a mock sandbox environment for testing."""
        from .mock_sandbox import MockSandbox
        return MockSandbox(constraints)
    
    def _cleanup_environment(self, environment: SandboxEnvironment):
        """Clean up and destroy a sandbox environment."""
        try:
            environment.cleanup()
            if environment in self.active_environments:
                self.active_environments.remove(environment)
            logger.info(f"Cleaned up sandbox environment: {environment.id}")
        except Exception as e:
            logger.error(f"Failed to cleanup environment {environment.id}: {e}")
    
    def cleanup_all(self):
        """Clean up all active environments."""
        for environment in self.active_environments.copy():
            self._cleanup_environment(environment)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about active environments."""
        return {
            'active_environments': len(self.active_environments),
            'docker_available': self.docker_available,
            'environments': [
                {
                    'id': env.id,
                    'status': env.status,
                    'created_at': env.created_at.isoformat() if env.created_at else None
                }
                for env in self.active_environments
            ]
        }