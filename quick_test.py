#!/usr/bin/env python3
"""Quick test script to verify setup without needing API keys."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.targets.llm_target import Message
from src.agents.base import ConversationTurn, AttackResult
from src.attacks.prompt_injection import PromptInjectionAttack
from benchmarks.harmbench_loader import HarmBenchLoader
from src.evaluator import BenchmarkEvaluator

print("=" * 80)
print("AGENTICREDTEAM - QUICK SETUP TEST")
print("=" * 80)

# Test 1: Imports
print("\n✓ All imports successful")

# Test 2: Data structures
print("\n✓ Testing data structures...")
msg = Message(role="user", content="Hello")
turn = ConversationTurn(prompt="Hi", response="Hello!", turn_number=1)
print(f"  - Message: {msg.role}")
print(f"  - Turn: #{turn.turn_number}")

# Test 3: Attack strategy (no LLM needed)
print("\n✓ Testing attack strategy...")
attack = PromptInjectionAttack()
prompt = attack.generate_attack_prompt(
    objective="test objective",
    conversation_history=[],
    turn_number=1
)
print(f"  - Generated prompt length: {len(prompt)} chars")

# Test 4: HarmBench loader (fallback mode)
print("\n✓ Testing HarmBench loader...")
loader = HarmBenchLoader()
behaviors = loader._get_fallback_behaviors()
print(f"  - Loaded {len(behaviors)} fallback behaviors")
print(f"  - Sample: {behaviors[0].behavior[:60]}...")

# Test 5: Evaluator
print("\n✓ Testing evaluator...")
evaluator = BenchmarkEvaluator(output_dir="results")

# Create dummy results
dummy_results = [
    AttackResult(
        success=True,
        conversation=[turn],
        final_prompt="test",
        final_response="test response",
        num_turns=1,
        safety_score=0.8,
        strategy_name="Test",
        metadata={}
    ),
    AttackResult(
        success=False,
        conversation=[turn],
        final_prompt="test2",
        final_response="test response2",
        num_turns=1,
        safety_score=0.2,
        strategy_name="Test",
        metadata={}
    )
]

metrics = evaluator.calculate_metrics(dummy_results)
print(f"  - ASR: {metrics.attack_success_rate:.1%}")
print(f"  - Avg score: {metrics.avg_safety_score:.2f}")

print("\n" + "=" * 80)
print("SETUP TEST PASSED!")
print("=" * 80)
print("\nNext steps:")
print("1. Set up your API keys in .env file")
print("2. Run: python main.py test-connection")
print("3. Run: python main.py benchmark --num-samples 5")
print("=" * 80)
