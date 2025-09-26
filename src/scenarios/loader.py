"""
Scenario Loader

Handles loading scenarios from various sources.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import json
import glob

from .scenario import Scenario

logger = logging.getLogger(__name__)


class ScenarioLoader:
    """
    Loads test scenarios from files and other sources.
    """
    
    @classmethod
    def load(cls, source: str) -> Scenario:
        """
        Load a single scenario from file.
        
        Args:
            source: Path to scenario file
            
        Returns:
            Loaded scenario
        """
        return Scenario.load(source)
    
    @classmethod
    def load_multiple(cls, pattern: str) -> List[Scenario]:
        """
        Load multiple scenarios matching a file pattern.
        
        Args:
            pattern: Glob pattern for scenario files
            
        Returns:
            List of loaded scenarios
        """
        scenarios = []
        for filepath in glob.glob(pattern):
            try:
                scenario = cls.load(filepath)
                scenarios.append(scenario)
                logger.info(f"Loaded scenario: {scenario.name}")
            except Exception as e:
                logger.error(f"Failed to load scenario from {filepath}: {e}")
        
        return scenarios
    
    @classmethod
    def load_from_directory(cls, directory: str, recursive: bool = True) -> List[Scenario]:
        """
        Load all scenarios from a directory.
        
        Args:
            directory: Directory containing scenario files
            recursive: Whether to search subdirectories
            
        Returns:
            List of loaded scenarios
        """
        pattern = "**/*.yaml" if recursive else "*.yaml"
        full_pattern = str(Path(directory) / pattern)
        return cls.load_multiple(full_pattern)
    
    @classmethod
    def load_by_category(cls, directory: str, category: str) -> List[Scenario]:
        """
        Load scenarios filtered by category.
        
        Args:
            directory: Directory to search
            category: Category to filter by
            
        Returns:
            List of scenarios in the specified category
        """
        all_scenarios = cls.load_from_directory(directory)
        return [s for s in all_scenarios if s.category == category]
    
    @classmethod
    def load_by_tags(cls, directory: str, tags: List[str], 
                    match_all: bool = False) -> List[Scenario]:
        """
        Load scenarios filtered by tags.
        
        Args:
            directory: Directory to search
            tags: Tags to filter by
            match_all: If True, scenario must have all tags; if False, any tag
            
        Returns:
            List of scenarios matching tag criteria
        """
        all_scenarios = cls.load_from_directory(directory)
        
        if match_all:
            return [s for s in all_scenarios 
                   if all(tag in s.tags for tag in tags)]
        else:
            return [s for s in all_scenarios 
                   if any(tag in s.tags for tag in tags)]
    
    @classmethod
    def validate_scenario_file(cls, filepath: str) -> Dict[str, Any]:
        """
        Validate a scenario file without fully loading it.
        
        Args:
            filepath: Path to scenario file
            
        Returns:
            Validation result with status and errors
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'filepath': filepath
        }
        
        try:
            # Check file exists and is readable
            path = Path(filepath)
            if not path.exists():
                result['errors'].append("File does not exist")
                return result
            
            if not path.is_file():
                result['errors'].append("Path is not a file")
                return result
            
            # Try to parse YAML/JSON
            with open(filepath, 'r') as f:
                if filepath.endswith('.json'):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['name', 'target', 'objective', 'attack_vectors']
            for field in required_fields:
                if field not in data or not data[field]:
                    result['errors'].append(f"Missing required field: {field}")
            
            # Validate attack vectors structure
            if 'attack_vectors' in data and isinstance(data['attack_vectors'], list):
                for i, vector in enumerate(data['attack_vectors']):
                    if not isinstance(vector, dict):
                        result['errors'].append(f"Attack vector {i} is not a dictionary")
                        continue
                    
                    if 'type' not in vector:
                        result['errors'].append(f"Attack vector {i} missing 'type' field")
                    
                    if 'payload' not in vector:
                        result['errors'].append(f"Attack vector {i} missing 'payload' field")
            
            # Validate timeout
            if 'timeout' in data:
                try:
                    timeout = int(data['timeout'])
                    if timeout <= 0:
                        result['warnings'].append("Timeout should be positive")
                    elif timeout > 3600:
                        result['warnings'].append("Timeout is very large (>1 hour)")
                except ValueError:
                    result['errors'].append("Timeout must be an integer")
            
            # Try to create scenario object
            if not result['errors']:
                scenario = Scenario.from_dict(data)
                if not scenario.is_valid():
                    result['errors'].append("Scenario validation failed")
                else:
                    result['valid'] = True
                    result['scenario_info'] = {
                        'name': scenario.name,
                        'category': scenario.category,
                        'severity': scenario.severity,
                        'attack_count': len(scenario.attack_vectors)
                    }
            
        except yaml.YAMLError as e:
            result['errors'].append(f"YAML parsing error: {e}")
        except json.JSONDecodeError as e:
            result['errors'].append(f"JSON parsing error: {e}")
        except Exception as e:
            result['errors'].append(f"Unexpected error: {e}")
        
        return result
    
    @classmethod
    def get_scenario_info(cls, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Get basic information about a scenario without full loading.
        
        Args:
            filepath: Path to scenario file
            
        Returns:
            Scenario metadata or None if invalid
        """
        validation = cls.validate_scenario_file(filepath)
        if validation['valid']:
            return validation['scenario_info']
        return None