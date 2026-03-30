"""Recon Agents - Specialized security scanning tools."""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from hiverecon.database import AgentType, Finding, FindingSeverity, ScanStatus


class BaseAgent(ABC):
    """Base class for all recon agents."""
    
    agent_type: AgentType
    
    def __init__(self, target: str, config: Optional[dict] = None):
        self.target = target
        self.config = config or {}
        self.output: Optional[str] = None
        self.error: Optional[str] = None
        self.findings: list[Finding] = []
    
    @abstractmethod
    async def execute(self) -> bool:
        """Execute the agent scan. Returns True if successful."""
        pass
    
    @abstractmethod
    def parse_output(self) -> list[Finding]:
        """Parse tool output into findings."""
        pass
    
    def get_command(self) -> str:
        """Get the command to execute."""
        raise NotImplementedError


class SubdomainAgent(BaseAgent):
    """Subdomain enumeration agent using subfinder/amass."""
    
    agent_type = AgentType.SUBDOMAIN
    
    def __init__(self, target: str, config: Optional[dict] = None):
        super().__init__(target, config)
        self.tool = self.config.get("tool", "subfinder")  # or "amass"
    
    def get_command(self) -> str:
        if self.tool == "amass":
            return f"amass enum -d {self.target} -silent"
        return f"subfinder -d {self.target} -silent -json"
    
    async def execute(self) -> bool:
        """Run subdomain enumeration."""
        try:
            process = await asyncio.create_subprocess_shell(
                self.get_command(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                self.output = stdout.decode()
                self.findings = self.parse_output()
                return True
            else:
                self.error = stderr.decode() if stderr else "No output"
                return False
                
        except Exception as e:
            self.error = str(e)
            return False
    
    def parse_output(self) -> list[Finding]:
        """Parse subdomain enumeration results."""
        findings = []
        
        if not self.output:
            return findings
        
        if self.tool == "subfinder":
            # Parse JSON output
            for line in self.output.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        finding = Finding(
                            agent_type=self.agent_type,
                            finding_type="subdomain",
                            severity=FindingSeverity.INFO,
                            title=f"Subdomain discovered: {data.get('host', 'unknown')}",
                            description=f"Discovered subdomain during enumeration",
                            evidence=data,
                            location=data.get("host", ""),
                        )
                        findings.append(finding)
                    except json.JSONDecodeError:
                        # Plain text output
                        finding = Finding(
                            agent_type=self.agent_type,
                            finding_type="subdomain",
                            severity=FindingSeverity.INFO,
                            title=f"Subdomain discovered: {line.strip()}",
                            description="Discovered subdomain during enumeration",
                            location=line.strip(),
                        )
                        findings.append(finding)
        else:
            # Plain text output (amass or fallback)
            for subdomain in self.output.strip().split("\n"):
                if subdomain:
                    finding = Finding(
                        agent_type=self.agent_type,
                        finding_type="subdomain",
                        severity=FindingSeverity.INFO,
                        title=f"Subdomain discovered: {subdomain.strip()}",
                        description="Discovered subdomain during enumeration",
                        location=subdomain.strip(),
                    )
                    findings.append(finding)
        
        return findings


class PortScanAgent(BaseAgent):
    """Port scanning agent using nmap."""
    
    agent_type = AgentType.PORT_SCAN
    
    def get_command(self) -> str:
        ports = self.config.get("ports", "-")
        return f"nmap -sV -sC -oN - -p {ports} {self.target}"
    
    async def execute(self) -> bool:
        """Run port scan."""
        try:
            process = await asyncio.create_subprocess_shell(
                self.get_command(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                self.output = stdout.decode()
                self.findings = self.parse_output()
                return True
            else:
                self.error = stderr.decode() if stderr else "No output"
                return False
                
        except Exception as e:
            self.error = str(e)
            return False
    
    def parse_output(self) -> list[Finding]:
        """Parse nmap output into findings."""
        findings = []
        
        if not self.output:
            return findings
        
        # Simple parsing - look for open ports
        current_port = None
        for line in self.output.split("\n"):
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if parts:
                    port = parts[0].split("/")[0]
                    service = " ".join(parts[2:]) if len(parts) > 2 else "unknown"
                    
                    severity = FindingSeverity.INFO
                    if port in ["21", "22", "23", "3389"]:
                        severity = FindingSeverity.LOW
                    elif port in ["1433", "3306", "5432", "27017"]:
                        severity = FindingSeverity.MEDIUM
                    
                    finding = Finding(
                        agent_type=self.agent_type,
                        finding_type="open_port",
                        severity=severity,
                        title=f"Open port {port} detected",
                        description=f"Service: {service}",
                        evidence={"port": port, "service": service, "raw": line},
                        location=f"{self.target}:{port}",
                    )
                    findings.append(finding)
        
        return findings


class EndpointDiscoveryAgent(BaseAgent):
    """Endpoint discovery agent using katana/ffuf."""
    
    agent_type = AgentType.ENDPOINT
    
    def __init__(self, target: str, config: Optional[dict] = None):
        super().__init__(target, config)
        self.tool = self.config.get("tool", "katana")  # or "ffuf"
        self.wordlist = self.config.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
    
    def get_command(self) -> str:
        if self.tool == "ffuf":
            return (
                f"ffuf -u https://{self.target}/FUZZ "
                f"-w {self.wordlist} -o stdout -of json"
            )
        return f"katana -u https://{self.target} -jc -silent -json"
    
    async def execute(self) -> bool:
        """Run endpoint discovery."""
        try:
            process = await asyncio.create_subprocess_shell(
                self.get_command(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                self.output = stdout.decode()
                self.findings = self.parse_output()
                return True
            else:
                self.error = stderr.decode() if stderr else "No output"
                return False
                
        except Exception as e:
            self.error = str(e)
            return False
    
    def parse_output(self) -> list[Finding]:
        """Parse endpoint discovery results."""
        findings = []
        
        if not self.output:
            return findings
        
        if self.tool == "katana":
            for line in self.output.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        url = data.get("endpoint", data.get("request", {}).get("url", ""))
                        if url:
                            finding = Finding(
                                agent_type=self.agent_type,
                                finding_type="endpoint",
                                severity=FindingSeverity.INFO,
                                title=f"Endpoint discovered",
                                description=f"Discovered endpoint during crawling",
                                evidence=data,
                                location=url,
                            )
                            findings.append(finding)
                    except json.JSONDecodeError:
                        continue
        else:
            # ffuf JSON output
            try:
                data = json.loads(self.output)
                for result in data.get("results", []):
                    url = result.get("url", "")
                    status = result.get("status", 0)
                    if url and status:
                        finding = Finding(
                            agent_type=self.agent_type,
                            finding_type="endpoint",
                            severity=FindingSeverity.INFO,
                            title=f"Endpoint discovered (HTTP {status})",
                            description=f"Discovered endpoint with status {status}",
                            evidence=result,
                            location=url,
                        )
                        findings.append(finding)
            except json.JSONDecodeError:
                pass
        
        return findings


class VulnerabilityScanAgent(BaseAgent):
    """Vulnerability scanning agent using nuclei."""
    
    agent_type = AgentType.VULNERABILITY
    
    def get_command(self) -> str:
        templates = self.config.get("templates", "")
        severity_filter = self.config.get("severity_filter", "")
        
        cmd = f"nuclei -u https://{self.target} -json"
        if templates:
            cmd += f" -t {templates}"
        if severity_filter:
            cmd += f" -severity {severity_filter}"
        return cmd
    
    async def execute(self) -> bool:
        """Run vulnerability scan."""
        try:
            process = await asyncio.create_subprocess_shell(
                self.get_command(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                self.output = stdout.decode()
                self.findings = self.parse_output()
                return True
            else:
                self.error = stderr.decode() if stderr else "No output"
                return False
                
        except Exception as e:
            self.error = str(e)
            return False
    
    def parse_output(self) -> list[Finding]:
        """Parse nuclei vulnerability scan results."""
        findings = []
        
        if not self.output:
            return findings
        
        for line in self.output.strip().split("\n"):
            if line:
                try:
                    data = json.loads(line)
                    severity_map = {
                        "critical": FindingSeverity.CRITICAL,
                        "high": FindingSeverity.HIGH,
                        "medium": FindingSeverity.MEDIUM,
                        "low": FindingSeverity.LOW,
                        "info": FindingSeverity.INFO,
                    }
                    
                    severity = severity_map.get(
                        data.get("info", {}).get("severity", "info").lower(),
                        FindingSeverity.INFO
                    )
                    
                    finding = Finding(
                        agent_type=self.agent_type,
                        finding_type="vulnerability",
                        severity=severity,
                        title=data.get("info", {}).get("name", "Unknown vulnerability"),
                        description=data.get("info", {}).get("description", ""),
                        evidence=data,
                        location=data.get("host", "") + data.get("matched-at", ""),
                    )
                    findings.append(finding)
                except json.JSONDecodeError:
                    continue
        
        return findings


class MCPServerAgent(BaseAgent):
    """
    MCP (Model Context Protocol) server agent for browser-based analysis.
    
    This agent uses MCP to perform deep browser-based bug analysis,
    including JavaScript execution, DOM analysis, and client-side vulnerability detection.
    """
    
    agent_type = AgentType.MCP
    
    def get_command(self) -> str:
        return f"mcp-client --target {self.target} --deep-analysis"
    
    async def execute(self) -> bool:
        """Run MCP-based analysis."""
        # Placeholder - actual MCP integration
        try:
            # Simulate MCP analysis
            self.output = f"MCP analysis completed for {self.target}"
            self.findings = self.parse_output()
            return True
        except Exception as e:
            self.error = str(e)
            return False
    
    def parse_output(self) -> list[Finding]:
        """Parse MCP analysis results."""
        # Placeholder - actual implementation will parse MCP output
        findings = []
        
        # Example: Client-side vulnerability detection
        finding = Finding(
            agent_type=self.agent_type,
            finding_type="mcp_analysis",
            severity=FindingSeverity.INFO,
            title="MCP Browser Analysis Completed",
            description="Deep browser-based analysis completed. Check for client-side vulnerabilities.",
            evidence={"target": self.target, "analysis_type": "browser-based"},
            location=f"https://{self.target}",
        )
        findings.append(finding)
        
        return findings


# Agent registry
AGENT_REGISTRY = {
    AgentType.SUBDOMAIN: SubdomainAgent,
    AgentType.PORT_SCAN: PortScanAgent,
    AgentType.ENDPOINT: EndpointDiscoveryAgent,
    AgentType.VULNERABILITY: VulnerabilityScanAgent,
    AgentType.MCP: MCPServerAgent,
}


def get_agent(agent_type: AgentType, target: str, config: Optional[dict] = None) -> BaseAgent:
    """Factory function to create agents."""
    agent_class = AGENT_REGISTRY.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return agent_class(target, config)
