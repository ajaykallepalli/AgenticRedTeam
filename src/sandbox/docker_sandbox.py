"""
Docker-based Sandbox Environment

Provides secure isolation using Docker containers.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import time

from .environment import SandboxEnvironment

logger = logging.getLogger(__name__)


class DockerSandbox(SandboxEnvironment):
    """
    Docker-based sandbox environment for secure test execution.
    """
    
    def __init__(self, docker_client, timeout: int = 300, memory_limit: str = "1GB",
                 network_isolation: bool = True, allowed_domains: List[str] = None):
        """
        Initialize Docker sandbox.
        
        Args:
            docker_client: Docker client instance
            timeout: Maximum execution time
            memory_limit: Container memory limit
            network_isolation: Whether to isolate network access
            allowed_domains: List of allowed domains for network access
        """
        super().__init__(timeout, memory_limit)
        self.docker_client = docker_client
        self.network_isolation = network_isolation
        self.allowed_domains = allowed_domains or []
        self.container = None
        self.network = None
        
    def initialize(self) -> bool:
        """Initialize the Docker container environment."""
        try:
            logger.info(f"Initializing Docker sandbox {self.id}")
            
            # Create isolated network if needed
            if self.network_isolation:
                self.network = self._create_network()
            
            # Create and start container
            self.container = self._create_container()
            self.container.start()
            
            # Wait for container to be ready
            self._wait_for_container_ready()
            
            self.status = "ready"
            self.created_at = datetime.now()
            
            logger.info(f"Docker sandbox {self.id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Docker sandbox: {e}")
            self.cleanup()
            return False
    
    def execute_attack(self, attack_vector: Dict[str, Any], target: str) -> Dict[str, Any]:
        """
        Execute attack vector in the Docker container.
        
        Args:
            attack_vector: Attack configuration
            target: Target system identifier
            
        Returns:
            Attack execution results
        """
        if not self.container or self.status != "ready":
            raise RuntimeError("Sandbox not ready for execution")
        
        start_time = time.time()
        
        try:
            # Prepare attack payload
            payload = self._prepare_payload(attack_vector, target)
            
            # Execute in container
            exec_result = self.container.exec_run(
                cmd=f"python /app/execute_attack.py '{json.dumps(payload)}'",
                timeout=self.timeout,
                demux=True
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            if exec_result.exit_code == 0:
                try:
                    stdout_output = exec_result.output[0].decode('utf-8')
                    result = json.loads(stdout_output)
                except (json.JSONDecodeError, AttributeError):
                    result = {'content': str(exec_result.output), 'raw': True}
            else:
                stderr_output = exec_result.output[1].decode('utf-8') if exec_result.output[1] else "Unknown error"
                result = {'error': stderr_output, 'exit_code': exec_result.exit_code}
            
            # Add metadata
            result.update({
                'execution_time': execution_time,
                'container_id': self.container.id[:12],
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Attack execution failed: {e}")
            return {
                'error': str(e),
                'execution_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def cleanup(self):
        """Clean up Docker resources."""
        logger.info(f"Cleaning up Docker sandbox {self.id}")
        
        try:
            if self.container:
                self.container.stop(timeout=10)
                self.container.remove()
                self.container = None
                
            if self.network:
                self.network.remove()
                self.network = None
                
            self.status = "destroyed"
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def _create_network(self):
        """Create isolated Docker network."""
        network_name = f"redteam-{self.id[:8]}"
        return self.docker_client.networks.create(
            name=network_name,
            driver="bridge",
            options={"com.docker.network.bridge.enable_icc": "false"}
        )
    
    def _create_container(self):
        """Create Docker container with security constraints."""
        container_config = {
            'image': 'python:3.9-slim',  # Base image
            'name': f"redteam-sandbox-{self.id[:8]}",
            'detach': True,
            'mem_limit': self.memory_limit,
            'memswap_limit': self.memory_limit,
            'cpu_period': 100000,
            'cpu_quota': 50000,  # 50% CPU limit
            'security_opt': ['no-new-privileges:true'],
            'cap_drop': ['ALL'],
            'cap_add': ['CHOWN', 'SETUID', 'SETGID'],
            'read_only': True,
            'tmpfs': {
                '/tmp': 'rw,noexec,nosuid,nodev,size=100m',
                '/var/tmp': 'rw,noexec,nosuid,nodev,size=50m'
            },
            'volumes': {
                # Mount attack execution script
                '/tmp/redteam_scripts': {'bind': '/app', 'mode': 'ro'}
            },
            'environment': {
                'PYTHONPATH': '/app',
                'HOME': '/tmp'
            },
            'working_dir': '/app',
            'user': 'nobody'
        }
        
        # Add network configuration
        if self.network:
            container_config['network'] = self.network.name
        elif self.network_isolation:
            container_config['network_mode'] = 'none'
        
        return self.docker_client.containers.create(**container_config)
    
    def _wait_for_container_ready(self, max_wait: int = 30):
        """Wait for container to be ready."""
        for _ in range(max_wait):
            if self.container.status == 'running':
                return
            time.sleep(1)
            self.container.reload()
        
        raise RuntimeError("Container failed to start within timeout")
    
    def _prepare_payload(self, attack_vector: Dict[str, Any], target: str) -> Dict[str, Any]:
        """Prepare attack payload for execution."""
        return {
            'attack_type': attack_vector.get('type', 'unknown'),
            'payload': attack_vector.get('payload', ''),
            'target': target,
            'options': attack_vector.get('options', {}),
            'constraints': {
                'timeout': self.timeout,
                'max_requests': 10,
                'allowed_domains': self.allowed_domains
            }
        }
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get actual memory usage from container stats."""
        if not self.container:
            return super()._get_memory_usage()
        
        try:
            stats = self.container.stats(stream=False)
            memory_stats = stats['memory_stats']
            
            usage = memory_stats.get('usage', 0)
            limit = memory_stats.get('limit', 0)
            
            return {
                'used': f"{usage // (1024*1024)}MB",
                'limit': f"{limit // (1024*1024)}MB",
                'percentage': (usage / limit * 100) if limit > 0 else 0
            }
        except Exception:
            return super()._get_memory_usage()
    
    def _get_cpu_usage(self) -> float:
        """Get actual CPU usage from container stats."""
        if not self.container:
            return super()._get_cpu_usage()
        
        try:
            stats = self.container.stats(stream=False)
            cpu_stats = stats['cpu_stats']
            precpu_stats = stats['precpu_stats']
            
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            
            if system_delta > 0:
                return (cpu_delta / system_delta) * len(cpu_stats['cpu_usage']['percpu_usage']) * 100
            
        except Exception:
            pass
        
        return super()._get_cpu_usage()