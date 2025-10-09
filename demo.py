#!/usr/bin/env python3
"""Demo script showing AgenticRedTeam capabilities (works with or without API keys)."""

import os
from dotenv import load_dotenv

load_dotenv()

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     AGENTICREDTEAM - DEMO                                    ║
║                                                                              ║
║  Autonomous Red Teaming for LLMs                                            ║
║  Inspired by DeepTeam with modern improvements                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# Check for API keys
has_openai = bool(os.getenv('OPENAI_API_KEY'))
has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))

print("API Key Status:")
print(f"  {'✓' if has_openai else '✗'} OpenAI:    {'Configured' if has_openai else 'Not configured'}")
print(f"  {'✓' if has_anthropic else '✗'} Anthropic: {'Configured' if has_anthropic else 'Not configured'}")

if not (has_openai or has_anthropic):
    print("\n⚠️  No API keys configured. Edit .env file to run live tests.")
    print("\nContinuing with offline demo...\n")

print("\n" + "="*80)
print("FEATURE SHOWCASE")
print("="*80)

# 1. Attack Strategies
print("\n1. ATTACK STRATEGIES")
print("-" * 80)

from src.attacks.prompt_injection import PromptInjectionAttack
from src.attacks.crescendo import CrescendoAttack
from src.targets.llm_target import LLMTarget

injection = PromptInjectionAttack()
print(f"\n✓ {injection.name}: {len(injection.ATTACK_TEMPLATES)} jailbreak templates")
print("  Templates include: Role-play, DAN-style, Authority claims, etc.")

sample_objective = "provide instructions for illegal activity"
sample_prompt = injection.generate_attack_prompt(sample_objective, [], 1)
print(f"\n  Example jailbreak prompt (truncated):")
print(f"  '{sample_prompt[:150]}...'")

# 2. HarmBench Dataset
print("\n\n2. HARMBENCH DATASET")
print("-" * 80)

from benchmarks.harmbench_loader import HarmBenchLoader

loader = HarmBenchLoader()
behaviors = loader._get_fallback_behaviors()
print(f"\n✓ Loaded {len(behaviors)} harmful behaviors for testing")

print("\n  Sample behaviors by category:")
categories = {}
for b in behaviors:
    if b.category not in categories:
        categories[b.category] = []
    categories[b.category].append(b.behavior)

for cat, behaves in list(categories.items())[:5]:
    print(f"\n  {cat}:")
    print(f"    - {behaves[0][:70]}...")

# 3. Evaluation System
print("\n\n3. EVALUATION & METRICS")
print("-" * 80)

from src.evaluator import BenchmarkEvaluator
from src.agents.base import AttackResult, ConversationTurn

evaluator = BenchmarkEvaluator()

# Create sample results
sample_results = [
    AttackResult(
        success=True,
        conversation=[
            ConversationTurn(prompt="Turn 1", response="Response 1", turn_number=1),
            ConversationTurn(prompt="Turn 2", response="Response 2", turn_number=2),
        ],
        final_prompt="Final attack prompt",
        final_response="Unsafe response provided",
        num_turns=2,
        safety_score=0.85,
        strategy_name="Crescendo",
        metadata={"objective": "test"}
    ),
    AttackResult(
        success=False,
        conversation=[
            ConversationTurn(prompt="Attack", response="I cannot help with that", turn_number=1),
        ],
        final_prompt="Attack prompt",
        final_response="I cannot help with that",
        num_turns=1,
        safety_score=0.1,
        strategy_name="DirectPrompt",
        metadata={"objective": "test"}
    ),
    AttackResult(
        success=True,
        conversation=[
            ConversationTurn(prompt="Jailbreak", response="Sure, here's how...", turn_number=1),
        ],
        final_prompt="Jailbreak attempt",
        final_response="Sure, here's how...",
        num_turns=1,
        safety_score=0.75,
        strategy_name="PromptInjection",
        metadata={"objective": "test"}
    ),
]

metrics = evaluator.calculate_metrics(sample_results)

print(f"\n✓ Calculated metrics from {metrics.total_attacks} sample attacks:")
print(f"  - Attack Success Rate: {metrics.attack_success_rate:.1%}")
print(f"  - Average Safety Score: {metrics.avg_safety_score:.2f}")
print(f"  - Avg Turns to Success: {metrics.avg_turns_to_success:.1f}")

print("\n  Per-strategy breakdown:")
for strategy, stats in metrics.metrics_by_strategy.items():
    print(f"    {strategy}: {stats['asr']:.0%} ASR ({stats['successful']}/{stats['total']})")

# 4. CLI Commands
print("\n\n4. AVAILABLE CLI COMMANDS")
print("-" * 80)

commands = [
    ("test-connection", "Verify API keys are working"),
    ("benchmark", "Run full red teaming benchmark"),
    ("single-attack", "Test a single attack for debugging"),
]

for cmd, desc in commands:
    print(f"\n  python main.py {cmd}")
    print(f"    → {desc}")

# 5. Next Steps
print("\n\n" + "="*80)
print("GETTING STARTED")
print("="*80)

print("\n1. Configure your API keys in .env file:")
print("   OPENAI_API_KEY=sk-...")
print("   ANTHROPIC_API_KEY=sk-ant-...")

print("\n2. Test your setup:")
print("   python main.py test-connection")

print("\n3. Run your first benchmark:")
print("   python main.py benchmark --num-samples 5 --strategies injection,direct")

print("\n4. Try a single attack:")
print('   python main.py single-attack --objective "your test objective" --strategy crescendo')

print("\n5. Read full documentation:")
print("   - README.md: Overview and architecture")
print("   - USAGE.md: Detailed usage guide and best practices")

print("\n" + "="*80)
print("KEY IMPROVEMENTS OVER DEEPTEAM")
print("="*80)

improvements = [
    "🎯 Agent Memory: Tracks conversation history for sophisticated attacks",
    "🔄 Adaptive Strategy: Crescendo learns from target responses",
    "🔌 Universal API: Single interface for all LLM providers (LiteLLM)",
    "💾 Attack Library: Template-based jailbreaks with 8+ patterns",
    "📊 Rich Metrics: Detailed per-strategy breakdowns and comparisons",
    "🎨 Lightweight: Minimal dependencies, pure Python",
    "⚡ Async Ready: Built-in async support for parallel attacks",
]

for imp in improvements:
    print(f"\n  {imp}")

print("\n" + "="*80)
print("\nDemo complete! Ready to red team your LLMs.\n")
print("="*80 + "\n")
