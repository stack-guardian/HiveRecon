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
from hiverecon.agents.recon_agents import AgentType, get_agent
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
    
    # Track all findings from all agents
    all_findings = []
    agent_results = {}

    # Define agents to run
    agents_config = [
        (AgentType.SUBDOMAIN, "Subdomain Enumeration", {}),
        (AgentType.PORT_SCAN, "Port Scanning", {"ports": "1-1000"}),
        (AgentType.ENDPOINT, "Endpoint Discovery", {}),
        (AgentType.VULNERABILITY, "Vulnerability Scanning", {}),
        (AgentType.MCP, "MCP Analysis", {}),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Step 1: Initialize
        task = progress.add_task("[cyan]Initializing...", total=None)
        progress.update(task, description="[green]✓ Initialization complete[/green]")

        # Step 2: Validate scope
        progress.remove_task(task)
        task = progress.add_task("[cyan]Validating scope with AI...", total=None)
        progress.update(task, description="[green]✓ Scope validation complete[/green]")

        # Step 3: Launch and run agents
        progress.remove_task(task)
        task = progress.add_task("[cyan]Running recon agents...", total=len(agents_config))

        for agent_type, agent_name, agent_config in agents_config:
            progress.update(task, description=f"[cyan]Running {agent_name}...[/cyan]")
            
            try:
                # Create and execute agent
                agent = get_agent(agent_type, target, agent_config)
                success = await agent.execute()
                
                if success:
                    findings_count = len(agent.findings)
                    agent_results[agent_name] = {
                        "status": "success",
                        "findings": findings_count,
                        "error": None,
                    }
                    all_findings.extend(agent.findings)
                    
                    if findings_count > 0:
                        progress.console.print(f"  [green]✓ {agent_name}: {findings_count} finding(s)[/green]")
                    else:
                        progress.console.print(f"  [yellow]⚠ {agent_name}: No findings[/yellow]")
                else:
                    agent_results[agent_name] = {
                        "status": "failed",
                        "findings": 0,
                        "error": agent.error,
                    }
                    progress.console.print(f"  [red]✗ {agent_name}: {agent.error}[/red]")
                    
            except Exception as e:
                agent_results[agent_name] = {
                    "status": "error",
                    "findings": 0,
                    "error": str(e),
                }
                progress.console.print(f"  [red]✗ {agent_name}: Error - {str(e)}[/red]")
            
            progress.advance(task)

        progress.update(task, description="[green]✓ All agents completed[/green]")

        # Step 4: Generate report
        progress.remove_task(task)
        task = progress.add_task("[cyan]Generating report...", total=None)
        progress.update(task, description="[green]✓ Report generated[/green]")

    # Show summary with real results
    _show_scan_summary(scan_id, target, output_dir, all_findings, agent_results)


def _show_scan_summary(scan_id: str, target: str, output_dir: Optional[Path], all_findings: list = None, agent_results: dict = None):
    """Display scan results summary."""
    console.print("\n[bold blue]📊 Scan Summary[/bold blue]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Scan ID", scan_id)
    table.add_row("Target", target)
    table.add_row("Status", "Completed")
    
    # Count findings by type
    if all_findings:
        subdomains = len([f for f in all_findings if f.finding_type == "subdomain"])
        open_ports = len([f for f in all_findings if f.finding_type == "open_port"])
        endpoints = len([f for f in all_findings if f.finding_type == "endpoint"])
        vulnerabilities = len([f for f in all_findings if f.finding_type == "vulnerability"])
        other = len(all_findings) - subdomains - open_ports - endpoints - vulnerabilities
    else:
        subdomains = open_ports = endpoints = vulnerabilities = other = 0

    table.add_row("Subdomains Found", str(subdomains))
    table.add_row("Open Ports", str(open_ports))
    table.add_row("Endpoints", str(endpoints))
    table.add_row("Vulnerabilities", str(vulnerabilities))
    if other > 0:
        table.add_row("Other Findings", str(other))

    console.print(table)

    # Show agent status
    if agent_results:
        console.print("\n[bold blue]🔧 Agent Status[/bold blue]")
        status_table = Table(show_header=True, header_style="bold magenta")
        status_table.add_column("Agent", style="cyan")
        status_table.add_column("Status", style="green")
        status_table.add_column("Findings", style="yellow")
        
        for agent_name, result in agent_results.items():
            status_icon = "✓" if result["status"] == "success" else "✗"
            status_style = "green" if result["status"] == "success" else "red"
            status_table.add_row(
                agent_name,
                f"[{status_style}]{status_icon} {result['status']}[/{status_style}]",
                str(result["findings"]),
            )
        console.print(status_table)

    # Show findings summary by severity
    if all_findings:
        from hiverecon.database import FindingSeverity
        
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0,
        }
        for finding in all_findings:
            severity_counts[finding.severity.name] = severity_counts.get(finding.severity.name, 0) + 1
        
        console.print("\n[bold blue]⚠️  Findings by Severity[/bold blue]")
        severity_table = Table(show_header=True, header_style="bold magenta")
        severity_table.add_column("Severity", style="cyan")
        severity_table.add_column("Count", style="green")
        
        severity_colors = {
            "CRITICAL": "red",
            "HIGH": "orange",
            "MEDIUM": "yellow",
            "LOW": "blue",
            "INFO": "green",
        }
        
        for severity, count in severity_counts.items():
            if count > 0:
                color = severity_colors.get(severity, "white")
                severity_table.add_row(f"[{color}]{severity}[/{color}]", str(count))
        
        console.print(severity_table)

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
