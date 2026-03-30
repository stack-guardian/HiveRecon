#!/usr/bin/env python3
"""
HiveRecon GUI - Simple Terminal Interface for Non-Technical Users
"""

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import box

console = Console()

# HiveRecon path
HIVERECON_PATH = Path("/home/vibhxr/hiverecon")
VENV_PYTHON = HIVERECON_PATH / "venv" / "bin" / "python"


def show_banner():
    """Display HiveRecon banner."""
    banner = """
    [bold blue]╔═══════════════════════════════════════════════════════════╗[/bold blue]
    [bold blue]║[/bold blue]  [bold green]🐝 HiveRecon Scanner[/bold green] - AI-Powered Reconnaissance   [bold blue]║[/bold blue]
    [bold blue]║[/bold blue]  [yellow]Bug Bounty Security Scanner[/yellow]                      [bold blue]║[/bold blue]
    [bold blue]╚═══════════════════════════════════════════════════════════╝[/bold blue]
    """
    console.print(banner)
    console.print()


def show_legal_disclaimer():
    """Display legal disclaimer."""
    disclaimer = """
[bold red]⚖️  LEGAL DISCLAIMER[/bold red]

HiveRecon is designed for [bold]AUTHORIZED[/bold] security research only.

By using this tool, you acknowledge:
• You have [bold]explicit authorization[/bold] to scan the target
• You will [bold]respect scope boundaries[/bold] at all times
• You are [bold]responsible for compliance[/bold] with applicable laws
• All actions are [bold]logged for accountability[/bold]

[red]Unauthorized scanning is ILLEGAL and violates the terms of use.[/red]
"""
    console.print(Panel(disclaimer, title="⚠️  Legal Notice", border_style="yellow"))
    console.print()


def check_nmap():
    """Check if nmap is working."""
    try:
        result = subprocess.run(
            ["nmap", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            return True, version
        else:
            return False, "nmap error"
    except Exception as e:
        return False, str(e)


def run_scan(target: str, quick_scan: bool = True):
    """Run HiveRecon scan on target."""
    console.print(f"\n[bold blue]🎯 Target:[/bold blue] {target}")
    
    # Check nmap status
    nmap_ok, nmap_info = check_nmap()
    if nmap_ok:
        console.print(f"[green]✓[/green] {nmap_info}")
    else:
        console.print(f"[red]✗[/red] nmap issue: {nmap_info}")
    
    console.print()
    
    # Run the scan
    port_range = "1-100" if quick_scan else "1-1000"
    cmd = [
        str(VENV_PYTHON), "-m", "hiverecon", "scan",
        "-t", target
    ]
    
    console.print("[bold]Starting scan...[/bold]\n")
    
    try:
        # Run with auto-confirm
        env = subprocess.os.environ.copy()
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(HIVERECON_PATH),
            env=env
        )
        
        # Send 'y' for confirmation
        stdout, _ = process.communicate(input='y\n', timeout=300)
        
        # Display output
        console.print(stdout)
        
    except subprocess.TimeoutExpired:
        process.kill()
        console.print("[red]Scan timed out (5 minutes)[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def show_quick_tools():
    """Show quick tool status."""
    console.print("\n[bold]🔧 Tool Status[/bold]\n")
    
    tools = [
        ("nmap", "Port Scanning"),
        ("curl", "HTTP Analysis"),
        ("subfinder", "Subdomain Enumeration"),
        ("katana", "Web Crawling"),
        ("nuclei", "Vulnerability Scan"),
    ]
    
    table = Table(box=box.SIMPLE)
    table.add_column("Tool", style="cyan")
    table.add_column("Purpose", style="white")
    table.add_column("Status", style="green")
    
    for tool, purpose in tools:
        try:
            result = subprocess.run(
                [tool, "--version"] if tool != "curl" else [tool, "--help"],
                capture_output=True,
                timeout=3
            )
            status = "[green]✓ Installed[/green]" if result.returncode == 0 else "[yellow]⚠ Issue[/yellow]"
        except:
            status = "[red]✗ Not Found[/red]"
        
        table.add_row(tool, purpose, status)
    
    console.print(table)


def main_menu():
    """Display main menu."""
    while True:
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("  [1] 🎯 Quick Scan (ports 1-100)")
        console.print("  [2] 🔍 Full Scan (ports 1-1000)")
        console.print("  [3] 🛠️  Check Tool Status")
        console.print("  [4] ℹ️  About")
        console.print("  [5] 🚪 Exit")
        console.print()
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "1":
            target = Prompt.ask("Enter target domain (e.g., example.com)")
            if target:
                show_legal_disclaimer()
                if Confirm.ask("Do you have authorization to scan this target?"):
                    run_scan(target, quick_scan=True)
                else:
                    console.print("[yellow]Scan cancelled. Always obtain authorization.[/yellow]")
                    
        elif choice == "2":
            target = Prompt.ask("Enter target domain (e.g., example.com)")
            if target:
                show_legal_disclaimer()
                if Confirm.ask("Do you have authorization to scan this target?"):
                    run_scan(target, quick_scan=False)
                else:
                    console.print("[yellow]Scan cancelled. Always obtain authorization.[/yellow]")
                    
        elif choice == "3":
            show_quick_tools()
            
        elif choice == "4":
            about_info = """
[bold]HiveRecon Scanner v0.1.0[/bold]

AI-powered reconnaissance framework for bug bounty hunting.

[bold]Features:[/bold]
• Port scanning with nmap
• HTTP security header analysis
• Subdomain enumeration
• Web crawling
• Vulnerability detection

[bold]Created by:[/bold] Stack Guardian
[bold]License:[/bold] MIT
"""
            console.print(Panel(about_info, title="About"))
            
        elif choice == "5":
            console.print("\n[green]Goodbye! Stay legal, stay safe! 🔒[/green]\n")
            break


def main():
    """Main entry point."""
    console.clear()
    show_banner()
    show_legal_disclaimer()
    
    if not Confirm.ask("Do you understand and agree to the legal terms?", default=False):
        console.print("[red]You must agree to the terms to use this tool.[/red]")
        sys.exit(1)
    
    main_menu()


if __name__ == "__main__":
    main()
