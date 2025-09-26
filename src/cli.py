#!/usr/bin/env python3
"""
Command Line Interface for Agentic Red-Team Manager
"""

import click
import logging
import sys
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .adversarial import RedTeamManager
from .scenarios import ScenarioLoader, ScenarioBuilder
from .reporting import ReportGenerator

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """Agentic Red-Team Manager - Automated adversarial testing for AI systems."""
    
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('scenario_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output directory for reports')
@click.option('--format', '-f', default='html', type=click.Choice(['html', 'json', 'pdf']))
@click.pass_context
def run(ctx, scenario_path: str, output: Optional[str], format: str):
    """Run an adversarial test scenario."""
    
    try:
        console.print(f"[blue]Loading scenario: {scenario_path}[/blue]")
        
        # Load scenario
        scenario = ScenarioLoader.load(scenario_path)
        console.print(f"[green]✓ Loaded scenario: {scenario.name}[/green]")
        
        # Initialize red team manager
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Initializing Red Team Manager...", total=None)
            manager = RedTeamManager(config_file=ctx.obj['config_file'])
            progress.update(task, description="[green]✓ Manager initialized[/green]")
            
            # Execute test
            progress.update(task, description="Executing adversarial test...")
            results = manager.execute_test(scenario)
            
            # Generate report
            progress.update(task, description="Generating report...")
            report_path = manager.generate_report([results], format)
            
            progress.update(task, description="[green]✓ Test completed[/green]")
        
        # Display summary
        _display_test_summary(results)
        
        console.print(f"\n[green]Report generated: {report_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--category', help='Filter scenarios by category')
@click.option('--severity', help='Filter scenarios by severity')
@click.option('--parallel', '-p', default=1, help='Number of parallel executions')
@click.option('--output', '-o', help='Output directory for reports')
@click.pass_context
def batch(ctx, directory: str, category: Optional[str], severity: Optional[str], 
          parallel: int, output: Optional[str]):
    """Run multiple scenarios from a directory."""
    
    try:
        console.print(f"[blue]Loading scenarios from: {directory}[/blue]")
        
        # Load scenarios
        scenarios = ScenarioLoader.load_from_directory(directory)
        
        # Apply filters
        if category:
            scenarios = [s for s in scenarios if s.category == category]
        if severity:
            scenarios = [s for s in scenarios if s.severity == severity]
        
        console.print(f"[green]✓ Found {len(scenarios)} scenarios[/green]")
        
        if not scenarios:
            console.print("[yellow]No scenarios found matching criteria[/yellow]")
            return
        
        # Initialize manager
        manager = RedTeamManager(config_file=ctx.obj['config_file'])
        
        # Execute scenarios
        all_results = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Running scenarios...", total=len(scenarios))
            
            for scenario in scenarios:
                progress.update(task, description=f"Running: {scenario.name}")
                try:
                    result = manager.execute_test(scenario)
                    all_results.append(result)
                    console.print(f"[green]✓ {scenario.name}[/green]")
                except Exception as e:
                    console.print(f"[red]✗ {scenario.name}: {str(e)}[/red]")
                
                progress.advance(task)
        
        # Generate consolidated report
        console.print("[blue]Generating consolidated report...[/blue]")
        report_path = manager.generate_report(all_results, 'html')
        
        # Display batch summary
        _display_batch_summary(all_results)
        
        console.print(f"\n[green]Batch report generated: {report_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--name', prompt='Scenario name', help='Name of the scenario')
@click.option('--target', prompt='Target system', help='Target system to test')
@click.option('--category', default='general', help='Scenario category')
@click.option('--output', '-o', help='Output file path')
def create(name: str, target: str, category: str, output: Optional[str]):
    """Create a new test scenario interactively."""
    
    try:
        console.print(f"[blue]Creating scenario: {name}[/blue]")
        
        # Get additional details
        description = click.prompt("Description", default="")
        objective = click.prompt("Attack objective", default="Test system safety")
        severity = click.prompt("Severity", default="medium", 
                              type=click.Choice(['low', 'medium', 'high', 'critical']))
        
        # Build scenario
        builder = ScenarioBuilder()
        scenario = (builder
                   .set_name(name)
                   .set_description(description)
                   .set_target(target)
                   .set_category(category)
                   .set_objective(objective)
                   .set_severity(severity)
                   .build())
        
        # Determine output path
        if not output:
            safe_name = name.lower().replace(' ', '_').replace('-', '_')
            output = f"{safe_name}.yaml"
        
        # Save scenario
        scenario.save(output)
        
        console.print(f"[green]✓ Scenario created: {output}[/green]")
        
        # Display scenario info
        table = Table(title="Scenario Details")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Name", scenario.name)
        table.add_row("Target", scenario.target)
        table.add_row("Category", scenario.category)
        table.add_row("Severity", scenario.severity)
        table.add_row("Objective", scenario.objective)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
def list(directory: str):
    """List available scenarios in a directory."""
    
    try:
        scenarios = ScenarioLoader.load_from_directory(directory)
        
        if not scenarios:
            console.print("[yellow]No scenarios found[/yellow]")
            return
        
        table = Table(title=f"Scenarios in {directory}")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Severity", style="red")
        table.add_column("Target", style="blue")
        
        for scenario in scenarios:
            table.add_row(
                scenario.name,
                scenario.category,
                scenario.severity,
                scenario.target
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('scenario_path', type=click.Path(exists=True))
def validate(scenario_path: str):
    """Validate a scenario file."""
    
    try:
        result = ScenarioLoader.validate_scenario_file(scenario_path)
        
        if result['valid']:
            console.print(f"[green]✓ Scenario is valid: {scenario_path}[/green]")
            
            info = result.get('scenario_info', {})
            table = Table(title="Scenario Information")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in info.items():
                table.add_row(key.replace('_', ' ').title(), str(value))
            
            console.print(table)
        else:
            console.print(f"[red]✗ Scenario is invalid: {scenario_path}[/red]")
            
            for error in result['errors']:
                console.print(f"  [red]• {error}[/red]")
            
            for warning in result['warnings']:
                console.print(f"  [yellow]• {warning}[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


def _display_test_summary(results: dict):
    """Display test summary in a formatted table."""
    
    table = Table(title="Test Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    scenario = results.get('scenario', {})
    safety = results.get('safety', {})
    assessment = safety.get('overall_assessment', {})
    
    table.add_row("Scenario", scenario.get('name', 'Unknown'))
    table.add_row("Success", "Yes" if results.get('success', False) else "No")
    table.add_row("Safety Score", f"{assessment.get('safety_score', 0)}/100")
    table.add_row("Risk Level", assessment.get('risk_level', 'unknown'))
    table.add_row("Vulnerability Found", "Yes" if assessment.get('vulnerability_detected', False) else "No")
    
    console.print(table)


def _display_batch_summary(results: List[dict]):
    """Display batch test summary."""
    
    total_tests = len(results)
    successful_attacks = sum(1 for r in results if r.get('success', False))
    avg_safety_score = sum(
        r.get('safety', {}).get('overall_assessment', {}).get('safety_score', 0) 
        for r in results
    ) / total_tests if total_tests > 0 else 0
    
    table = Table(title="Batch Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Tests", str(total_tests))
    table.add_row("Successful Attacks", str(successful_attacks))
    table.add_row("Success Rate", f"{successful_attacks/total_tests*100:.1f}%" if total_tests > 0 else "0%")
    table.add_row("Average Safety Score", f"{avg_safety_score:.1f}/100")
    
    console.print(table)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()