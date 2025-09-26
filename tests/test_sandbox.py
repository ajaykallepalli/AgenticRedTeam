"""
Tests for sandbox functionality.
"""

import pytest
from unittest.mock import Mock, patch

from src.sandbox import SandboxManager
from src.sandbox.mock_sandbox import MockSandbox


class TestSandboxManager:
    """Test SandboxManager functionality."""
    
    def test_manager_initialization(self):
        """Test sandbox manager initialization."""
        config = {
            'timeout': 300,
            'memory_limit': '1GB',
            'network_isolation': True
        }
        
        manager = SandboxManager(config)
        assert manager.default_timeout == 300
        assert manager.memory_limit == '1GB'
        assert manager.network_isolation is True
    
    @patch('docker.from_env')
    def test_docker_availability_check(self, mock_docker):
        """Test Docker availability checking."""
        # Test when Docker is available
        mock_docker.return_value = Mock()
        manager = SandboxManager({})
        assert manager.docker_available is True
        
        # Test when Docker is not available
        mock_docker.side_effect = Exception("Docker not found")
        manager = SandboxManager({})
        assert manager.docker_available is False
    
    def test_environment_creation_fallback(self):
        """Test environment creation falls back to mock when Docker unavailable."""
        config = {'timeout': 300}
        manager = SandboxManager(config)
        manager.docker_available = False
        
        with manager.create_environment() as env:
            assert env is not None
            assert isinstance(env, MockSandbox)


class TestMockSandbox:
    """Test MockSandbox functionality."""
    
    def test_mock_sandbox_initialization(self):
        """Test mock sandbox initialization."""
        constraints = {'timeout': 60}
        sandbox = MockSandbox(constraints)
        
        assert sandbox.timeout == 60
        assert sandbox.status == "initializing"
    
    def test_mock_sandbox_lifecycle(self):
        """Test mock sandbox lifecycle."""
        sandbox = MockSandbox({})
        
        # Test initialization
        assert sandbox.initialize()
        assert sandbox.status == "ready"
        
        # Test execution
        attack_vector = {
            'type': 'prompt_injection',
            'payload': 'test payload'
        }
        
        result = sandbox.execute_attack(attack_vector, 'test-target')
        assert 'content' in result
        assert 'execution_time' in result
        assert result['mock'] is True
        
        # Test cleanup
        sandbox.cleanup()
        assert sandbox.status == "destroyed"
    
    def test_mock_response_generation(self):
        """Test mock response generation for different attack types."""
        sandbox = MockSandbox({})
        sandbox.initialize()
        
        # Test different attack types
        attack_types = ['prompt_injection', 'jailbreak', 'data_extraction']
        
        for attack_type in attack_types:
            attack_vector = {
                'type': attack_type,
                'payload': f'test {attack_type} payload'
            }
            
            result = sandbox.execute_attack(attack_vector, 'test-target')
            assert isinstance(result['content'], str)
            assert len(result['content']) > 0


if __name__ == "__main__":
    pytest.main([__file__])