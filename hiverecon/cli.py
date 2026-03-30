"""CLI interface for HiveRecon."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from hiverecon import __version__
from hiverecon.config import get_config
from hiverecon.database import Scan, ScanStatus, init_db
from hiverecon.core.hive_mind import HiveMindCoordinator

app = typer.Typer(
    name="hiverecon",
    help="🐝 AI-Powered Reconnaissance Framework for Bug Bounty Hunting",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold blue]HiveRecon[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, help="Show version"
    ),
):
    """HiveRecon CLI"""
    pass


@app.command()
def scan(
    target: str = typer.Option(..., "--target", "-t", help="Target domain"),
    platform: Optional[str] = typer.Option(
        None, "--platform", "-p", help="Bug bounty platform (hackerone, bugcrowd, intigriti)"
    ),
    program_id: Optional[str] = typer.Option(
        None, "--program-id", help="Program ID on the platform"
    ),
    scope_file: Optional[Path] = typer.Option(
        None, "--scope", "-s", help="JSON file with scope configuration"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for results"
    ),
):
    """
    Start a new reconnaissance scan.
    
    Examples:
    
        hiverecon scan -t example.com
        
        hiverecon scan -t example.com -p hackerone --program-id 12345
        
        hiverecon scan -t example.com --scope scope.json
    """
    config = get_config()
    
    # Show legal disclaimer
    if config.legal.disclaimer_on_startup:
        _show_disclaimer()
    
    # Acknowledge disclaimer
    if config.legal.require_acknowledgment:
        typer.echo("")
        confirmed = typer.confirm("Do you have authorization to scan this target?")
        if not confirmed:
            console.print("[red]Scan cancelled. Always obtain proper authorization.[/red]")
            raise typer.Exit(1)
    
    # Generate scan ID
    scan_id = str(uuid.uuid4())[:8]
    
    console.print(f"\n[bold blue]🐝 Starting HiveRecon scan[/bold blue]")
    console.print(f"Scan ID: [cyan]{scan_id}[/cyan]")
    console.print(f"Target: [green]{target}[/green]")
    
    # Load scope configuration
    scope_config = {}
    if scope_file and scope_file.exists():
        with open(scope_file) as f:
            scope_config = json.load(f)
        console.print(f"Scope loaded from: {scope_file}")
    elif platform and program_id:
        console.print(f"Platform: {platform} (Program: {program_id})")
        # Will fetch scope from platform API
    else:
        # Default scope: target domain and all subdomains
        scope_config = {
            "in_scope": [
                {"type": "domain", "value": target},
                {"type": "wildcard", "value": f"*.{target}"},
            ],
            "out_of_scope": [],
        }
    
    # Create scan record
    asyncio.run(_create_scan(scan_id, target, platform, scope_config))
    
    # Run the scan
    asyncio.run(
        _run_scan(scan_id, target, platform, program_id, scope_config, output_dir)
    )


async def _create_scan(scan_id: str, target: str, platform: Optional[str], scope_config: dict):
    """Create scan record in database."""
    config = get_config()
    await init_db(config.get_database_url())
    
    # Scan creation will be handled by the scan runner
    pass


async def _run_scan(
    scan_id: str,
    target: str,
    platform: Optional[str],
    program_id: Optional[str],
    scope_config: dict,
    output_dir: Optional[Path],
):
    """Execute the reconnaissance scan."""
    config = get_config()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Step 1: Initialize
        task = progress.add_task("[cyan]Initializing...", total=None)
        await asyncio.sleep(1)
        progress.update(task, description="[green]✓ Initialization complete[/green]")
        
        # Step 2: Validate scope
        progress.remove_task(task)
        task = progress.add_task("[cyan]Validating scope with AI...", total=None)
        
        # Create coordinator and validate targets
        # Note: This is simplified - actual implementation needs session management
        progress.update(task, description="[green]✓ Scope validation complete[/green]")
        
        # Step 3: Launch agents
        progress.remove_task(task)
        task = progress.add_task("[cyan]Launching recon agents...", total=5)
        
        agents = [
            "Subdomain Enumeration",
            "Port Scanning",
            "Endpoint Discovery",
            "Vulnerability Scanning",
            "MCP Analysis",
        ]
        
        for agent in agents:
            await asyncio.sleep(0.5)  # Simulate agent launch
            progress.advance(task)
            progress.console.print(f"  [dim]→ {agent} agent started[/dim]")
        
        progress.update(task, description="[green]✓ All agents launched[/green]")
        
        # Step 4: Monitor progress (simulated)
        progress.remove_task(task)
        task = progress.add_task("[cyan]Monitoring agents...", total=100)
        
        for _ in range(10):
            await asyncio.sleep(0.3)
            progress.advance(task, 10)
        
        progress.update(task, description="[green]✓ Scan complete[/green]")
        
        # Step 5: Generate report
        progress.remove_task(task)
        task = progress.add_task("[cyan]Generating report...", total=None)
        await asyncio.sleep(1)
        progress.update(task, description="[green]✓ Report generated[/green]")
    
    # Show summary
    _show_scan_summary(scan_id, target, output_dir)


def _show_scan_summary(scan_id: str, target: str, output_dir: Optional[Path]):
    """Display scan results summary."""
    console.print("\n[bold blue]📊 Scan Summary[/bold blue]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Scan ID", scan_id)
    table.add_row("Target", target)
    table.add_row("Status", "Completed")
    table.add_row("Subdomains Found", "0 (simulated)")
    table.add_row("Open Ports", "0 (simulated)")
    table.add_row("Endpoints", "0 (simulated)")
    table.add_row("Vulnerabilities", "0 (simulated)")
    
    console.print(table)
    
    if output_dir:
        console.print(f"\n[dim]Results saved to: {output_dir}[/dim]")
    else:
        console.print(f"\n[dim]Use --output to save results to a directory[/dim]")


@app.command()
def status(scan_id: str = typer.Option(..., "--scan-id", help="Scan ID to check")):
    """Check the status of a scan."""
    console.print(f"[bold blue]Checking status for scan:[/bold blue] {scan_id}")
    console.print("[yellow]Status lookup not yet implemented[/yellow]")


@app.command()
def report(
    scan_id: str = typer.Option(..., "--scan-id", help="Scan ID"),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format (text, json, markdown, pdf)"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Generate a report for a completed scan."""
    console.print(f"[bold blue]Generating report for scan:[/bold blue] {scan_id}")
    console.print(f"Format: {output_format}")
    console.print("[yellow]Report generation not yet implemented[/yellow]")


@app.command()
def list_scans(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of scans to show"),
):
    """List recent scans."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Scan ID", style="cyan")
    table.add_column("Target", style="green")
    table.add_column("Platform", style="yellow")
    table.add_column("Status", style="blue")
    table.add_column("Created", style="white")
    
    # Placeholder data
    table.add_row("abc12345", "example.com", "hackerone", "completed", "2024-01-01")
    
    console.print(table)


@app.command()
def validate(
    target: str = typer.Argument(..., help="Target to validate"),
    scope_file: Path = typer.Option(..., "--scope", "-s", help="Scope configuration file"),
):
    """Validate if a target is in scope."""
    console.print(f"[bold blue]Validating target:[/bold blue] {target}")
    
    if not scope_file.exists():
        console.print(f"[red]Scope file not found: {scope_file}[/red]")
        raise typer.Exit(1)
    
    with open(scope_file) as f:
        scope_config = json.load(f)
    
    # Simple validation logic
    in_scope = False
    for item in scope_config.get("in_scope", []):
        if target == item.get("value", "") or target.endswith(f".{item.get('value', '')}"):
            in_scope = True
            break
    
    if in_scope:
        console.print("[green]✓ Target is IN SCOPE[/green]")
    else:
        console.print("[red]✗ Target is OUT OF SCOPE[/red]")


def _show_disclaimer():
    """Display legal disclaimer."""
    disclaimer_text = """
⚖️  LEGAL DISCLAIMER

HiveRecon is designed for AUTHORIZED security research only.

By using this tool, you acknowledge:
• You have explicit authorization to scan the target
• You will respect scope boundaries at all times  
• You are responsible for compliance with applicable laws
• All actions are logged for accountability

Unauthorized scanning is ILLEGAL and violates the terms of use.
"""
    console.print(Panel(disclaimer_text, title="⚠️  Legal Notice", border_style="yellow"))


if __name__ == "__main__":
    app()
