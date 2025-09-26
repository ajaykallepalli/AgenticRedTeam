"""
Tests for scenario management functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.scenarios import Scenario, ScenarioBuilder, ScenarioLoader


class TestScenario:
    """Test Scenario class functionality."""
    
    def test_scenario_creation(self):
        """Test basic scenario creation."""
        scenario = Scenario(
            name="Test Scenario",
            target="test-model",
            objective="Test objective"
        )
        
        assert scenario.name == "Test Scenario"
        assert scenario.target == "test-model"
        assert scenario.objective == "Test objective"
        assert scenario.id is not None
    
    def test_scenario_validation(self):
        """Test scenario validation."""
        # Valid scenario
        valid_scenario = Scenario(
            name="Valid Test",
            target="test-model",
            objective="Test objective"
        )
        valid_scenario.add_attack_vector("test", "test payload")
        assert valid_scenario.is_valid()
        
        # Invalid scenario (missing attack vectors)
        invalid_scenario = Scenario(
            name="Invalid Test",
            target="test-model",
            objective="Test objective"
        )
        assert not invalid_scenario.is_valid()
    
    def test_scenario_serialization(self):
        """Test scenario to_dict and from_dict."""
        original = Scenario(
            name="Serialization Test",
            target="test-model",
            objective="Test serialization"
        )
        original.add_attack_vector("test", "test payload")
        
        # Convert to dict and back
        data = original.to_dict()
        restored = Scenario.from_dict(data)
        
        assert restored.name == original.name
        assert restored.target == original.target
        assert restored.objective == original.objective
        assert len(restored.attack_vectors) == len(original.attack_vectors)


class TestScenarioBuilder:
    """Test ScenarioBuilder functionality."""
    
    def test_fluent_api(self):
        """Test fluent API construction."""
        scenario = (ScenarioBuilder()
                   .set_name("Builder Test")
                   .set_target("test-model")
                   .set_objective("Test builder")
                   .add_attack_vector("test", "test payload")
                   .build())
        
        assert scenario.name == "Builder Test"
        assert scenario.target == "test-model"
        assert scenario.objective == "Test builder"
        assert len(scenario.attack_vectors) == 1
    
    def test_preset_builders(self):
        """Test preset builder methods."""
        # Test prompt injection preset
        scenario = (ScenarioBuilder
                   .prompt_injection("test-model")
                   .build())
        
        assert "prompt_injection" in scenario.name.lower()
        assert scenario.category == "prompt_injection"
        assert len(scenario.attack_vectors) > 0
    
    def test_validation_on_build(self):
        """Test validation during build."""
        # Should raise ValueError for invalid scenario
        with pytest.raises(ValueError):
            (ScenarioBuilder()
             .set_name("Invalid")
             .build_and_validate())


class TestScenarioLoader:
    """Test ScenarioLoader functionality."""
    
    def test_scenario_file_validation(self):
        """Test scenario file validation."""
        # Create a temporary valid scenario file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
name: "Test Scenario"
target: "test-model"
objective: "Test objective"
attack_vectors:
  - type: "test"
    payload: "test payload"
""")
            temp_path = f.name
        
        try:
            result = ScenarioLoader.validate_scenario_file(temp_path)
            assert result['valid']
            assert len(result['errors']) == 0
        finally:
            os.unlink(temp_path)
    
    def test_invalid_scenario_file(self):
        """Test validation of invalid scenario file."""
        # Create a temporary invalid scenario file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
name: "Invalid Scenario"
# Missing required fields
""")
            temp_path = f.name
        
        try:
            result = ScenarioLoader.validate_scenario_file(temp_path)
            assert not result['valid']
            assert len(result['errors']) > 0
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__])