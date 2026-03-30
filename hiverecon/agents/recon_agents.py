"""Recon Agents - Specialized security scanning tools."""

import asyncio
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from hiverecon.database import AgentType, Finding, FindingSeverity, ScanStatus


def check_binary(name: str) -> bool:
    """Check if a binary is available on the system."""
    return shutil.which(name) is not None


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
        self.tool = self.config.get("tool", "auto")  # auto, subfinder, or amass

    def get_command(self) -> list:
        """Get subfinder/amass command as list for subprocess."""
        if self.tool == "amass":
            return ["amass", "enum", "-d", self.target, "-silent"]
        return ["subfinder", "-d", self.target, "-silent", "-json"]

    async def execute(self) -> bool:
        """Run subdomain enumeration using subprocess with auto-fallback."""
        try:
            # Auto-detect: try subfinder first, then amass
            if self.tool == "auto":
                if check_binary("subfinder"):
                    self.tool = "subfinder"
                elif check_binary("amass"):
                    self.tool = "amass"
                else:
                    self.error = "Neither subfinder nor amass is installed. Install one: go install github.com/projectdiscovery/subfinder or yay -S amass"
                    return False
            elif not check_binary(self.tool):
                install_cmd = "go install github.com/projectdiscovery/subfinder@latest" if self.tool == "subfinder" else "yay -S amass"
                self.error = f"{self.tool} is not installed. Install with: {install_cmd}"
                return False
            
            cmd = self.get_command()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.stdout:
                self.output = result.stdout
                self.findings = self.parse_output()
                return True
            else:
                self.error = result.stderr if result.stderr else "No output"
                return False

        except subprocess.TimeoutExpired:
            self.error = "Subdomain enumeration timed out after 300 seconds"
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
            # Parse JSON output (one JSON object per line)
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
                        # Plain text output fallback
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

    def get_command(self) -> list:
        """Get nmap command as list for subprocess."""
        ports = self.config.get("ports", "1-100")  # Default to top 100 ports for speed
        return ["nmap", "-sV", "-oX", "-", "-p", ports, self.target]

    async def execute(self) -> bool:
        """Run port scan using subprocess."""
        try:
            if not check_binary("nmap"):
                self.error = "nmap is not installed. Run: sudo pacman -S nmap"
                return False
            cmd = self.get_command()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.stdout:
                self.output = result.stdout
                self.findings = self.parse_output()
                return True
            else:
                self.error = result.stderr if result.stderr else "No output"
                return False

        except subprocess.TimeoutExpired:
            self.error = "Nmap scan timed out after 300 seconds"
            return False
        except Exception as e:
            self.error = str(e)
            return False

    def parse_output(self) -> list[Finding]:
        """Parse nmap XML output into findings."""
        findings = []

        if not self.output:
            return findings

        try:
            root = ET.fromstring(self.output)
            
            for host in root.findall(".//host"):
                # Get host address
                addr_elem = host.find("address")
                if addr_elem is not None:
                    ip_addr = addr_elem.get("addr", "unknown")
                else:
                    ip_addr = "unknown"

                # Get ports
                ports_elem = host.find("ports")
                if ports_elem is not None:
                    for port_elem in ports_elem.findall("port"):
                        port_id = port_elem.get("portid", "unknown")
                        protocol = port_elem.get("protocol", "tcp")
                        
                        state_elem = port_elem.find("state")
                        if state_elem is not None and state_elem.get("state") == "open":
                            service_elem = port_elem.find("service")
                            service_name = "unknown"
                            service_product = ""
                            service_version = ""
                            
                            if service_elem is not None:
                                service_name = service_elem.get("name", "unknown")
                                service_product = service_elem.get("product", "")
                                service_version = service_elem.get("version", "")
                            
                            service_info = service_name
                            if service_product:
                                service_info = f"{service_product} {service_version}".strip()
                            
                            # Determine severity based on port
                            severity = FindingSeverity.INFO
                            if port_id in ["21", "22", "23", "3389"]:
                                severity = FindingSeverity.LOW
                            elif port_id in ["1433", "3306", "5432", "27017"]:
                                severity = FindingSeverity.MEDIUM

                            finding = Finding(
                                agent_type=self.agent_type,
                                finding_type="open_port",
                                severity=severity,
                                title=f"Open port {port_id}/{protocol} detected",
                                description=f"Service: {service_info}",
                                evidence={
                                    "ip": ip_addr,
                                    "port": port_id,
                                    "protocol": protocol,
                                    "service": service_name,
                                    "product": service_product,
                                    "version": service_version,
                                },
                                location=f"{ip_addr}:{port_id}",
                            )
                            findings.append(finding)
        except ET.ParseError as e:
            # Fallback to simple text parsing if XML parsing fails
            findings.extend(self._parse_text_output())
        except Exception as e:
            self.error = f"Error parsing nmap output: {str(e)}"

        return findings

    def _parse_text_output(self) -> list[Finding]:
        """Fallback text-based parsing for nmap output."""
        findings = []
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
        self.tool = self.config.get("tool", "auto")  # auto, katana, or ffuf
        self.wordlist = self.config.get("wordlist", "/usr/share/wordlists/dirb/common.txt")

    def get_command(self) -> list:
        """Get endpoint discovery command as list for subprocess."""
        if self.tool == "ffuf":
            return ["ffuf", "-u", f"https://{self.target}/FUZZ",
                    "-w", self.wordlist, "-o", "stdout", "-of", "json"]
        return ["katana", "-u", f"https://{self.target}", "-jc", "-silent", "-json"]

    async def execute(self) -> bool:
        """Run endpoint discovery using subprocess with auto-detection."""
        try:
            # Auto-detect: try katana first, then ffuf
            if self.tool == "auto":
                if check_binary("katana"):
                    self.tool = "katana"
                elif check_binary("ffuf"):
                    self.tool = "ffuf"
                else:
                    self.error = "Neither katana nor ffuf is installed. Install: go install github.com/projectdiscovery/katana or yay -S ffuf"
                    return False
            elif not check_binary(self.tool):
                install_cmd = "go install github.com/projectdiscovery/katana@latest" if self.tool == "katana" else "yay -S ffuf"
                self.error = f"{self.tool} is not installed. Install with: {install_cmd}"
                return False
            
            # Validate wordlist for ffuf
            if self.tool == "ffuf" and not os.path.exists(self.wordlist):
                self.error = f"Wordlist not found: {self.wordlist}"
                return False
            
            result = subprocess.run(
                self.get_command(),
                capture_output=True, text=True, timeout=300
            )
            if result.stdout:
                self.output = result.stdout
                self.findings = self.parse_output()
                return True
            else:
                self.error = result.stderr or "No output"
                return False
        except subprocess.TimeoutExpired:
            self.error = "Endpoint discovery timed out"
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

    def get_command(self) -> list:
        """Get nuclei command as list for subprocess."""
        cmd = ["nuclei", "-u", f"https://{self.target}", "-json"]
        templates = self.config.get("templates", "")
        severity_filter = self.config.get("severity_filter", "")
        if templates:
            cmd += ["-t", templates]
        if severity_filter:
            cmd += ["-severity", severity_filter]
        return cmd

    async def execute(self) -> bool:
        """Run vulnerability scan using subprocess."""
        try:
            if not check_binary("nuclei"):
                self.error = "nuclei is not installed. Install with: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
                return False
            result = subprocess.run(
                self.get_command(),
                capture_output=True, text=True, timeout=300
            )
            if result.stdout:
                self.output = result.stdout
                self.findings = self.parse_output()
                return True
            else:
                self.error = result.stderr or "No output"
                return False
        except subprocess.TimeoutExpired:
            self.error = "Vulnerability scan timed out"
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
    """Browser-based analysis using curl for HTTP header security analysis."""

    agent_type = AgentType.MCP

    def get_command(self, scheme: str = "https") -> list:
        return ["curl", "-sI", "--connect-timeout", "15", "--max-time", "30", f"{scheme}://{self.target}"]

    async def execute(self) -> bool:
        """Run HTTP header check using subprocess, trying HTTPS first then HTTP."""
        try:
            if not check_binary("curl"):
                self.error = "curl is not installed."
                return False
            
            # Try HTTPS first, then fall back to HTTP
            self.output = ""
            for scheme in ["https", "http"]:
                try:
                    result = subprocess.run(
                        self.get_command(scheme),
                        capture_output=True, text=True, timeout=30
                    )
                    if result.stdout and "HTTP/" in result.stdout:
                        self.output = result.stdout
                        self.findings = self.parse_output()
                        return True
                except subprocess.TimeoutExpired:
                    continue
            
            self.error = "Both HTTPS and HTTP connection attempts timed out"
            return False
            
        except subprocess.TimeoutExpired:
            self.error = "HTTP header check timed out"
            return False
        except Exception as e:
            self.error = str(e)
            return False

    def parse_output(self) -> list[Finding]:
        """Parse HTTP headers for security analysis."""
        findings = []
        if not self.output:
            return findings

        headers = {}
        for line in self.output.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                headers[key.strip().lower()] = value.strip()

        security_headers = {
            "x-frame-options": "Missing X-Frame-Options header (clickjacking risk)",
            "x-content-type-options": "Missing X-Content-Type-Options header",
            "strict-transport-security": "Missing HSTS header",
            "content-security-policy": "Missing Content-Security-Policy header",
        }

        for header, message in security_headers.items():
            if header not in headers:
                findings.append(Finding(
                    agent_type=self.agent_type,
                    finding_type="missing_security_header",
                    severity=FindingSeverity.LOW,
                    title=message,
                    description=f"The {header} header was not found in the HTTP response.",
                    evidence={"headers_found": list(headers.keys())},
                    location=f"https://{self.target}",
                ))

        if not findings:
            findings.append(Finding(
                agent_type=self.agent_type,
                finding_type="header_analysis",
                severity=FindingSeverity.INFO,
                title="HTTP security headers look good",
                description="All major security headers are present.",
                evidence={"headers": headers},
                location=f"https://{self.target}",
            ))

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
