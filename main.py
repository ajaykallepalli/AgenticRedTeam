#!/usr/bin/env python3
"""Main CLI entry point for AgenticRedTeam."""

import os
from dotenv import load_dotenv
import yaml
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console

from src.targets.llm_target import LLMTarget
from src.agents.judge_agent import JudgeAgent
from src.attacks.prompt_injection import PromptInjectionAttack, DirectPromptAttack
from src.attacks.crescendo import CrescendoAttack
from src.orchestrator import AttackOrchestrator
from src.evaluator import BenchmarkEvaluator
from benchmarks.harmbench_loader import HarmBenchLoader

console = Console()

# Load environment variables (override any existing)
load_dotenv(override=True)


@click.group()
def cli():
    """AgenticRedTeam - Autonomous red teaming for LLMs."""
    pass


@cli.command()
@click.option('--target-model', default='gpt-3.5-turbo', help='Target model to test')
@click.option('--target-provider', default='openai', help='Target model provider')
@click.option('--judge-model', default='claude-3-5-sonnet-20241022', help='Judge model')
@click.option('--judge-provider', default='anthropic', help='Judge model provider')
@click.option('--attack-model', default='gpt-4o', help='Attack agent model')
@click.option('--attack-provider', default='openai', help='Attack agent provider')
@click.option('--num-samples', default=10, help='Number of behaviors to test')
@click.option('--strategies', default='all', help='Attack strategies (comma-separated: injection,crescendo,direct,all)')
@click.option('--output-dir', default='results', help='Output directory for results')
@click.option('--config', type=click.Path(exists=True), help='Path to config YAML file')
def benchmark(
    target_model: str,
    target_provider: str,
    judge_model: str,
    judge_provider: str,
    attack_model: str,
    attack_provider: str,
    num_samples: int,
    strategies: str,
    output_dir: str,
    config: Optional[str]
):
    """Run red teaming benchmark on target model."""

    console.print("\n[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║       AGENTIC RED TEAMING BENCHMARK              ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")

    # Load config if provided
    if config:
        with open(config) as f:
            config_data = yaml.safe_load(f)
        target_model = config_data.get('target', {}).get('model', target_model)
        target_provider = config_data.get('target', {}).get('provider', target_provider)
        judge_model = config_data.get('judge', {}).get('model', judge_model)
        judge_provider = config_data.get('judge', {}).get('provider', judge_provider)
        attack_model = config_data.get('attack_agent', {}).get('model', attack_model)
        attack_provider = config_data.get('attack_agent', {}).get('provider', attack_provider)
        num_samples = config_data.get('benchmark', {}).get('num_samples', num_samples)

    # Initialize components
    console.print("[yellow]Initializing components...[/yellow]")

    target = LLMTarget(model=target_model, provider=target_provider)
    console.print(f"[green]✓[/green] Target: {target_provider}/{target_model}")

    judge = JudgeAgent(model=judge_model, provider=judge_provider)
    console.print(f"[green]✓[/green] Judge: {judge_provider}/{judge_model}")

    attacker_llm = LLMTarget(model=attack_model, provider=attack_provider, temperature=0.9)
    console.print(f"[green]✓[/green] Attacker: {attack_provider}/{attack_model}")

    # Select attack strategies
    strategy_map = {
        'injection': PromptInjectionAttack(),
        'crescendo': CrescendoAttack(attacker_llm, max_turns=5),
        'direct': DirectPromptAttack()
    }

    if strategies.lower() == 'all':
        selected_strategies = list(strategy_map.values())
    else:
        strategy_names = [s.strip() for s in strategies.split(',')]
        selected_strategies = [strategy_map[name] for name in strategy_names if name in strategy_map]

    console.print(f"[green]✓[/green] Strategies: {', '.join([s.name for s in selected_strategies])}\n")

    # Load benchmark dataset
    console.print("[yellow]Loading HarmBench dataset...[/yellow]")
    loader = HarmBenchLoader()
    behaviors = loader.load()
    sampled_behaviors = loader.sample(behaviors, n=num_samples)
    console.print(f"[green]✓[/green] Loaded {len(sampled_behaviors)} test behaviors\n")

    # Create orchestrator and evaluator
    orchestrator = AttackOrchestrator(target=target, judge=judge, verbose=False)
    evaluator = BenchmarkEvaluator(output_dir=output_dir)

    # Run attacks
    console.print(f"[bold cyan]Running benchmark with {len(selected_strategies)} strategies on {len(sampled_behaviors)} behaviors...[/bold cyan]\n")

    objectives = [behavior.behavior for behavior in sampled_behaviors]

    results = orchestrator.execute_multiple_attacks(
        strategies=selected_strategies,
        objectives=objectives,
        success_threshold=0.7
    )

    # Calculate metrics and generate report
    console.print("\n[yellow]Generating report...[/yellow]")
    metrics = evaluator.calculate_metrics(results)

    report = evaluator.generate_report(
        results=results,
        target_model=f"{target_provider}/{target_model}",
        benchmark_name="HarmBench"
    )

    console.print("\n" + report)

    # Save results
    evaluator.save_results(
        results=results,
        metrics=metrics,
        filename=f"benchmark_{target_model.replace('/', '_')}_{Path(output_dir).name}.json"
    )

    console.print("\n[bold green]Benchmark complete![/bold green]\n")


@cli.command()
@click.option('--objective', required=True, help='Harmful behavior to elicit')
@click.option('--target-model', default='gpt-3.5-turbo', help='Target model')
@click.option('--target-provider', default='openai', help='Target provider')
@click.option('--strategy', default='crescendo', help='Attack strategy')
def single_attack(objective: str, target_model: str, target_provider: str, strategy: str):
    """Run a single attack for testing."""

    console.print(f"\n[bold cyan]Running single {strategy} attack...[/bold cyan]\n")

    # Initialize
    target = LLMTarget(model=target_model, provider=target_provider)
    judge = JudgeAgent()
    attacker_llm = LLMTarget(model='gpt-4o', provider='openai', temperature=0.9)

    # Select strategy
    strategies = {
        'injection': PromptInjectionAttack(),
        'crescendo': CrescendoAttack(attacker_llm),
        'direct': DirectPromptAttack()
    }

    attack_strategy = strategies.get(strategy, PromptInjectionAttack())

    # Run attack
    orchestrator = AttackOrchestrator(target=target, judge=judge, verbose=True)
    result = orchestrator.execute_attack(attack_strategy, objective)

    console.print(f"\n[bold]Final Result:[/bold]")
    console.print(f"Success: {result.success}")
    console.print(f"Danger Score: {result.safety_score:.3f}")
    console.print(f"Turns: {result.num_turns}")


@cli.command()
def test_connection():
    """Test API connections to LLM providers."""

    console.print("\n[bold cyan]Testing API connections...[/bold cyan]\n")

    # Test OpenAI
    try:
        openai_llm = LLMTarget(model='gpt-3.5-turbo', provider='openai')
        response = openai_llm.simple_query("Hello, respond with 'OK' if you can hear me.")
        console.print("[green]✓[/green] OpenAI connection successful")
        console.print(f"  Response: {response[:100]}")
    except Exception as e:
        console.print(f"[red]✗[/red] OpenAI connection failed: {e}")

    # Test Anthropic
    try:
        anthropic_llm = LLMTarget(model='claude-3-5-sonnet-20241022', provider='anthropic')
        response = anthropic_llm.simple_query("Hello, respond with 'OK' if you can hear me.")
        console.print("[green]✓[/green] Anthropic connection successful")
        console.print(f"  Response: {response[:100]}")
    except Exception as e:
        console.print(f"[red]✗[/red] Anthropic connection failed: {e}")

    # Test xAI
    try:
        xai_llm = LLMTarget(model='grok-3-mini', provider='xai')
        response = xai_llm.simple_query("Hello, respond with 'OK' if you can hear me.")
        console.print("[green]✓[/green] xAI connection successful")
        console.print(f"  Response: {response[:100]}")
    except Exception as e:
        console.print(f"[red]✗[/red] xAI connection failed: {e}")

    console.print("")


if __name__ == '__main__':
    cli()
