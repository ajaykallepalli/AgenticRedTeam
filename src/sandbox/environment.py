"""
Sandbox Environment Base Class

Abstract base class for all sandbox environments.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class SandboxEnvironment(ABC):
    """
    Abstract base class for sandbox environments.
    
    Provides isolation and safety for executing adversarial tests.
    """
    
    def __init__(self, timeout: int = 300, memory_limit: str = "1GB"):
        """
        Initialize the sandbox environment.
        
        Args:
            timeout: Maximum execution time in seconds
            memory_limit: Memory limit for the environment
        """
        self.id = str(uuid.uuid4())
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.created_at: Optional[datetime] = None
        self.status = "initializing"
        self.metrics: Dict[str, Any] = {}
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the sandbox environment.
        
        Returns:
            True if initialization was successful
        """
        pass
    
    @abstractmethod
    def execute_attack(self, attack_vector: Dict[str, Any], target: str) -> Dict[str, Any]:
        """
        Execute an attack vector against the target.
        
        Args:
            attack_vector: The attack to execute
            target: The target system/model
            
        Returns:
            Dictionary containing the response and metadata
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up the sandbox environment."""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance and usage metrics."""
        return {
            'id': self.id,
            'status': self.status,
            'uptime': self._get_uptime(),
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage(),
            **self.metrics
        }
    
    def _get_uptime(self) -> float:
        """Get environment uptime in seconds."""
        if not self.created_at:
            return 0.0
        return (datetime.now() - self.created_at).total_seconds()
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        # Placeholder implementation
        return {'used': '0MB', 'limit': self.memory_limit}
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        # Placeholder implementation
        return 0.0
    
    def is_healthy(self) -> bool:
        """Check if the environment is healthy and responsive."""
        return self.status in ['running', 'ready']