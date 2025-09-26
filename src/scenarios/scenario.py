"""
Scenario Data Model

Represents an adversarial test scenario with all its components.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import yaml


@dataclass
class Scenario:
    """
    Represents a complete adversarial test scenario.
    
    Contains all information needed to execute an adversarial test,
    including attack vectors, targets, objectives, and constraints.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: str = "general"
    severity: str = "medium"  # low, medium, high, critical
    
    # Core test components
    target: str = ""  # Target system/model identifier
    objective: str = ""  # What the attack aims to achieve
    attack_vectors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution constraints
    constraints: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # Maximum execution time in seconds
    max_iterations: int = 10
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    author: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: str = "1.0"
    
    # Success criteria
    success_criteria: List[str] = field(default_factory=list)
    expected_vulnerabilities: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize computed fields after object creation."""
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def add_attack_vector(self, attack_type: str, payload: str, 
                         options: Optional[Dict[str, Any]] = None):
        """
        Add an attack vector to this scenario.
        
        Args:
            attack_type: Type of attack (e.g., 'prompt_injection')
            payload: Attack payload/content
            options: Additional attack options
        """
        attack_vector = {
            'type': attack_type,
            'payload': payload,
            'options': options or {}
        }
        self.attack_vectors.append(attack_vector)
        self.updated_at = datetime.now()
    
    def add_constraint(self, name: str, value: Any):
        """
        Add an execution constraint.
        
        Args:
            name: Constraint name
            value: Constraint value
        """
        self.constraints[name] = value
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str):
        """Add a tag to this scenario."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def is_valid(self) -> bool:
        """
        Check if the scenario is valid for execution.
        
        Returns:
            True if scenario has all required components
        """
        required_fields = [self.name, self.target, self.objective]
        return all(field.strip() for field in required_fields) and len(self.attack_vectors) > 0
    
    def get_estimated_duration(self) -> int:
        """
        Estimate scenario execution duration in seconds.
        
        Returns:
            Estimated duration based on attack vectors and constraints
        """
        base_time = 30  # Base overhead
        vector_time = len(self.attack_vectors) * 10  # 10s per vector
        iteration_time = self.max_iterations * 5  # 5s per iteration
        
        estimated = base_time + vector_time + iteration_time
        return min(estimated, self.timeout)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert scenario to dictionary representation.
        
        Returns:
            Dictionary representation of the scenario
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'severity': self.severity,
            'target': self.target,
            'objective': self.objective,
            'attack_vectors': self.attack_vectors,
            'constraints': self.constraints,
            'timeout': self.timeout,
            'max_iterations': self.max_iterations,
            'tags': self.tags,
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'version': self.version,
            'success_criteria': self.success_criteria,
            'expected_vulnerabilities': self.expected_vulnerabilities,
            'estimated_duration': self.get_estimated_duration(),
            'is_valid': self.is_valid()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scenario':
        """
        Create scenario from dictionary representation.
        
        Args:
            data: Dictionary containing scenario data
            
        Returns:
            Scenario instance
        """
        # Handle datetime parsing
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            description=data.get('description', ''),
            category=data.get('category', 'general'),
            severity=data.get('severity', 'medium'),
            target=data.get('target', ''),
            objective=data.get('objective', ''),
            attack_vectors=data.get('attack_vectors', []),
            constraints=data.get('constraints', {}),
            timeout=data.get('timeout', 300),
            max_iterations=data.get('max_iterations', 10),
            tags=data.get('tags', []),
            author=data.get('author', ''),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get('version', '1.0'),
            success_criteria=data.get('success_criteria', []),
            expected_vulnerabilities=data.get('expected_vulnerabilities', [])
        )
    
    def save(self, filepath: str):
        """
        Save scenario to YAML file.
        
        Args:
            filepath: Path where to save the scenario
        """
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'Scenario':
        """
        Load scenario from YAML file.
        
        Args:
            filepath: Path to the scenario file
            
        Returns:
            Loaded scenario instance
        """
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    def clone(self, new_name: Optional[str] = None) -> 'Scenario':
        """
        Create a copy of this scenario.
        
        Args:
            new_name: Name for the cloned scenario
            
        Returns:
            Cloned scenario with new ID
        """
        data = self.to_dict()
        data['id'] = str(uuid.uuid4())
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = data['created_at']
        
        if new_name:
            data['name'] = new_name
        else:
            data['name'] = f"{self.name} (Copy)"
        
        return self.from_dict(data)