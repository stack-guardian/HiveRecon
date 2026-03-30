#!/usr/bin/env python3
"""
Test script to verify recon tool execution.

Run this after installing tools to verify they work.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hiverecon.agents.recon_agents import (
    SubdomainAgent,
    PortScanAgent,
    EndpointDiscoveryAgent,
    VulnerabilityScanAgent,
)


async def test_subfinder():
    """Test subfinder execution."""
    print("\n=== Testing SubdomainAgent (subfinder) ===")
    
    agent = SubdomainAgent("example.com", {"tool": "subfinder"})
    
    # Check if tool exists
    import shutil
    if not shutil.which("subfinder"):
        print("SKIP: subfinder not installed")
        print("Install: go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
        return False
    
    success = await agent.execute()
    
    if success:
        print(f"SUCCESS: Found {len(agent.findings)} subdomains")
        if agent.findings:
            print(f"Sample: {agent.findings[0].value}")
        return True
    else:
        print(f"FAILED: {agent.error}")
        return False


async def test_nmap():
    """Test nmap execution."""
    print("\n=== Testing PortScanAgent (nmap) ===")
    
    agent = PortScanAgent("example.com")
    
    import shutil
    if not shutil.which("nmap"):
        print("SKIP: nmap not installed")
        print("Install: sudo pacman -S nmap")
        return False
    
    # Quick scan (just top 10 ports)
    agent.config["ports"] = "80,443"
    success = await agent.execute()
    
    if success:
        print(f"SUCCESS: Found {len(agent.findings)} open ports")
        for finding in agent.findings:
            print(f"  - {finding.location}: {finding.description}")
        return True
    else:
        print(f"FAILED: {agent.error}")
        return False


async def test_katana():
    """Test katana execution."""
    print("\n=== Testing EndpointDiscoveryAgent (katana) ===")
    
    agent = EndpointDiscoveryAgent("example.com", {"tool": "katana"})
    
    import shutil
    if not shutil.which("katana"):
        print("SKIP: katana not installed")
        print("Install: go install github.com/projectdiscovery/katana/cmd/katana@latest")
        return False
    
    success = await agent.execute()
    
    if success:
        print(f"SUCCESS: Found {len(agent.findings)} endpoints")
        if agent.findings:
            print(f"Sample: {agent.findings[0].location}")
        return True
    else:
        print(f"FAILED: {agent.error}")
        return False


async def test_nuclei():
    """Test nuclei execution."""
    print("\n=== Testing VulnerabilityScanAgent (nuclei) ===")
    
    agent = VulnerabilityScanAgent("example.com")
    
    import shutil
    if not shutil.which("nuclei"):
        print("SKIP: nuclei not installed")
        print("Install: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")
        return False
    
    # Quick scan with info templates only
    agent.config["severity_filter"] = "info"
    success = await agent.execute()
    
    if success:
        print(f"SUCCESS: Found {len(agent.findings)} findings")
        if agent.findings:
            print(f"Sample: {agent.findings[0].title} ({agent.findings[0].severity})")
        return True
    else:
        print(f"FAILED: {agent.error}")
        return False


async def main():
    """Run all tests."""
    print("HiveRecon Tool Execution Tests")
    print("=" * 50)
    
    results = {
        "subfinder": await test_subfinder(),
        "nmap": await test_nmap(),
        "katana": await test_katana(),
        "nuclei": await test_nuclei(),
    }
    
    print("\n" + "=" * 50)
    print("Summary:")
    for tool, success in results.items():
        status = "PASS" if success else "FAIL/SKIP"
        print(f"  {tool}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    return 0 if passed > 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
