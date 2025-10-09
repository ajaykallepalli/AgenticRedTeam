"""Base classes for agents and attack strategies."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from src.targets.llm_target import LLMTarget, Message


class ConversationTurn(BaseModel):
    """Single turn in a conversation."""
    prompt: str = Field(..., description="Prompt sent to target")
    response: str = Field(..., description="Response from target")
    turn_number: int = Field(..., description="Turn number in conversation")


class AttackResult(BaseModel):
    """Result of an attack attempt."""
    success: bool = Field(..., description="Whether attack succeeded")
    conversation: List[ConversationTurn] = Field(..., description="Full conversation history")
    final_prompt: str = Field(..., description="Final attack prompt")
    final_response: str = Field(..., description="Final target response")
    num_turns: int = Field(..., description="Number of turns taken")
    safety_score: float = Field(..., description="Safety score from judge (0=safe, 1=unsafe)")
    strategy_name: str = Field(..., description="Name of attack strategy used")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class AttackStrategy(ABC):
    """Base class for attack strategies."""

    def __init__(
        self,
        attacker_llm: LLMTarget,
        max_turns: int = 5,
        name: str = "BaseAttack"
    ):
        """Initialize attack strategy.

        Args:
            attacker_llm: LLM to use for generating attacks
            max_turns: Maximum conversation turns
            name: Strategy name
        """
        self.attacker_llm = attacker_llm
        self.max_turns = max_turns
        self.name = name

    @abstractmethod
    def generate_attack_prompt(
        self,
        objective: str,
        conversation_history: List[ConversationTurn],
        turn_number: int
    ) -> str:
        """Generate next attack prompt.

        Args:
            objective: The harmful behavior to elicit
            conversation_history: Previous conversation turns
            turn_number: Current turn number

        Returns:
            Attack prompt to send to target
        """
        pass

    def should_continue(
        self,
        conversation_history: List[ConversationTurn],
        turn_number: int
    ) -> bool:
        """Determine if attack should continue.

        Args:
            conversation_history: Previous conversation turns
            turn_number: Current turn number

        Returns:
            True if should continue attacking
        """
        return turn_number < self.max_turns


class SingleTurnAttack(AttackStrategy):
    """Base class for single-turn attacks."""

    def __init__(self, attacker_llm: LLMTarget, name: str = "SingleTurn"):
        """Initialize single-turn attack."""
        super().__init__(attacker_llm, max_turns=1, name=name)

    def should_continue(
        self,
        conversation_history: List[ConversationTurn],
        turn_number: int
    ) -> bool:
        """Single-turn attacks never continue."""
        return False


class MultiTurnAttack(AttackStrategy):
    """Base class for multi-turn attacks."""

    def __init__(
        self,
        attacker_llm: LLMTarget,
        max_turns: int = 5,
        name: str = "MultiTurn"
    ):
        """Initialize multi-turn attack."""
        super().__init__(attacker_llm, max_turns=max_turns, name=name)
