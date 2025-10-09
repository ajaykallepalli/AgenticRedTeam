"""Evaluation and reporting for red teaming results."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from src.agents.base import AttackResult
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from collections import defaultdict


class BenchmarkMetrics(BaseModel):
    """Aggregated metrics for benchmark evaluation."""
    total_attacks: int = Field(..., description="Total number of attacks")
    successful_attacks: int = Field(..., description="Number of successful attacks")
    attack_success_rate: float = Field(..., description="ASR: % of successful attacks")
    avg_safety_score: float = Field(..., description="Average danger score")
    avg_turns_to_success: float = Field(..., description="Avg turns for successful attacks")
    metrics_by_strategy: Dict[str, Dict] = Field(default_factory=dict, description="Per-strategy metrics")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class BenchmarkEvaluator:
    """Evaluates and reports on red teaming benchmark results."""

    def __init__(self, output_dir: str = "results"):
        """Initialize evaluator.

        Args:
            output_dir: Directory to save results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def calculate_metrics(self, results: List[AttackResult]) -> BenchmarkMetrics:
        """Calculate aggregate metrics from attack results.

        Args:
            results: List of attack results

        Returns:
            BenchmarkMetrics object
        """
        if not results:
            return BenchmarkMetrics(
                total_attacks=0,
                successful_attacks=0,
                attack_success_rate=0.0,
                avg_safety_score=0.0,
                avg_turns_to_success=0.0
            )

        total = len(results)
        successful = sum(1 for r in results if r.success)
        asr = successful / total if total > 0 else 0.0
        avg_score = sum(r.safety_score for r in results) / total

        # Calculate avg turns to success (only for successful attacks)
        successful_results = [r for r in results if r.success]
        avg_turns = (
            sum(r.num_turns for r in successful_results) / len(successful_results)
            if successful_results else 0.0
        )

        # Per-strategy metrics
        strategy_results = defaultdict(list)
        for result in results:
            strategy_results[result.strategy_name].append(result)

        metrics_by_strategy = {}
        for strategy_name, strat_results in strategy_results.items():
            strat_successful = sum(1 for r in strat_results if r.success)
            strat_total = len(strat_results)
            strat_asr = strat_successful / strat_total if strat_total > 0 else 0.0
            strat_avg_score = sum(r.safety_score for r in strat_results) / strat_total

            metrics_by_strategy[strategy_name] = {
                "total": strat_total,
                "successful": strat_successful,
                "asr": strat_asr,
                "avg_safety_score": strat_avg_score
            }

        return BenchmarkMetrics(
            total_attacks=total,
            successful_attacks=successful,
            attack_success_rate=asr,
            avg_safety_score=avg_score,
            avg_turns_to_success=avg_turns,
            metrics_by_strategy=metrics_by_strategy
        )

    def save_results(
        self,
        results: List[AttackResult],
        metrics: BenchmarkMetrics,
        filename: str = "benchmark_results.json",
        save_detailed: bool = True
    ) -> Path:
        """Save results to JSON file.

        Args:
            results: List of attack results
            metrics: Calculated metrics
            filename: Output filename
            save_detailed: Save detailed conversation logs

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename

        output_data = {
            "metrics": metrics.model_dump(),
            "summary": {
                "total_attacks": metrics.total_attacks,
                "attack_success_rate": f"{metrics.attack_success_rate:.2%}",
                "avg_safety_score": f"{metrics.avg_safety_score:.3f}",
                "avg_turns_to_success": f"{metrics.avg_turns_to_success:.2f}"
            }
        }

        if save_detailed:
            output_data["detailed_results"] = [
                {
                    "success": r.success,
                    "strategy": r.strategy_name,
                    "num_turns": r.num_turns,
                    "safety_score": r.safety_score,
                    "objective": r.metadata.get("objective", ""),
                    "conversation": [
                        {
                            "turn": turn.turn_number,
                            "prompt": turn.prompt,
                            "response": turn.response
                        }
                        for turn in r.conversation
                    ]
                }
                for r in results
            ]

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Results saved to: {output_path}")
        return output_path

    def generate_report(
        self,
        results: List[AttackResult],
        target_model: str = "unknown",
        benchmark_name: str = "HarmBench"
    ) -> str:
        """Generate human-readable report.

        Args:
            results: List of attack results
            target_model: Name of target model
            benchmark_name: Name of benchmark dataset

        Returns:
            Formatted report string
        """
        metrics = self.calculate_metrics(results)

        report = f"""
{'='*80}
AGENTIC RED TEAMING BENCHMARK REPORT
{'='*80}

Target Model:     {target_model}
Benchmark:        {benchmark_name}
Timestamp:        {metrics.timestamp}
Total Attacks:    {metrics.total_attacks}

{'='*80}
OVERALL METRICS
{'='*80}

Attack Success Rate (ASR):     {metrics.attack_success_rate:.2%}
Successful Attacks:            {metrics.successful_attacks}/{metrics.total_attacks}
Average Danger Score:          {metrics.avg_safety_score:.3f} (0=safe, 1=unsafe)
Avg Turns to Success:          {metrics.avg_turns_to_success:.2f}

{'='*80}
METRICS BY ATTACK STRATEGY
{'='*80}

"""

        for strategy_name, strat_metrics in metrics.metrics_by_strategy.items():
            report += f"""
{strategy_name}:
  - Total attacks:        {strat_metrics['total']}
  - Successful:           {strat_metrics['successful']}
  - Success rate:         {strat_metrics['asr']:.2%}
  - Avg danger score:     {strat_metrics['avg_safety_score']:.3f}
"""

        report += f"\n{'='*80}\n"

        # Save report to file
        report_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"Report saved to: {report_path}")
        return report

    def compare_results(
        self,
        results_a: List[AttackResult],
        results_b: List[AttackResult],
        label_a: str = "Model A",
        label_b: str = "Model B"
    ) -> str:
        """Compare results from two different runs.

        Args:
            results_a: First set of results
            results_b: Second set of results
            label_a: Label for first model
            label_b: Label for second model

        Returns:
            Comparison report
        """
        metrics_a = self.calculate_metrics(results_a)
        metrics_b = self.calculate_metrics(results_b)

        report = f"""
{'='*80}
COMPARISON REPORT: {label_a} vs {label_b}
{'='*80}

Metric                          {label_a:>20s}    {label_b:>20s}    Difference
{'-'*80}
Attack Success Rate             {metrics_a.attack_success_rate:>19.2%}    {metrics_b.attack_success_rate:>19.2%}    {(metrics_b.attack_success_rate - metrics_a.attack_success_rate):>+10.2%}
Avg Danger Score                {metrics_a.avg_safety_score:>19.3f}    {metrics_b.avg_safety_score:>19.3f}    {(metrics_b.avg_safety_score - metrics_a.avg_safety_score):>+10.3f}
Avg Turns to Success            {metrics_a.avg_turns_to_success:>19.2f}    {metrics_b.avg_turns_to_success:>19.2f}    {(metrics_b.avg_turns_to_success - metrics_a.avg_turns_to_success):>+10.2f}

{'-'*80}

Summary:
- {label_a} had {metrics_a.successful_attacks}/{metrics_a.total_attacks} successful attacks
- {label_b} had {metrics_b.successful_attacks}/{metrics_b.total_attacks} successful attacks

"""

        if metrics_a.attack_success_rate < metrics_b.attack_success_rate:
            report += f"\n{label_a} is MORE ROBUST (lower ASR is better)\n"
        elif metrics_a.attack_success_rate > metrics_b.attack_success_rate:
            report += f"\n{label_b} is MORE ROBUST (lower ASR is better)\n"
        else:
            report += f"\nBoth models have EQUAL robustness\n"

        report += f"{'='*80}\n"

        return report
