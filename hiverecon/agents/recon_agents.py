"""Recon Agents - Specialized security scanning tools."""

import asyncio
import json
import os
import shutil
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
            if self.tool == "auto":
                if check_binary("subfinder"):
                    self.tool = "subfinder"
                elif check_binary("amass"):
                    self.tool = "amass"
                else:
                    self.error = "Neither subfinder nor amass is installed."
                    return False
            elif not check_binary(self.tool):
                self.error = f"{self.tool} is not installed."
                return False

            cmd = self.get_command()
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                self.error = "Subdomain enumeration timed out after 300 seconds"
                return False

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
    """Port scanning agent using nmap with batching and timeout support."""

    agent_type = AgentType.PORT_SCAN

    def __init__(self, targets: list[str] | str, config: Optional[dict] = None):
        """Initialize with a list of targets or a single target string."""
        if isinstance(targets, str):
            self.targets = [targets]
        else:
            self.targets = targets
        
        # Initialize BaseAgent with the first target as a representative
        rep_target = self.targets[0] if self.targets else "multiple-targets"
        super().__init__(rep_target, config)
        self.results: list[dict[str, Any]] = []

    def get_command(self, targets: list[str]) -> list[str]:
        """Get nmap command as list for subprocess."""
        # Use specific ports requested: 80,443,8080,8443,8888,3000,5000,9090
        ports = self.config.get("ports", "80,443,8080,8443,8888,3000,5000,9090")
        return ["nmap", "-sV", "-sC", "-T4", "--open", "-oX", "-", "-p", ports] + targets

    async def execute(self) -> list[dict[str, Any]]:
        """
        Run port scan on targets in batches of 5.
        Returns a list of dicts: [{host, port, service, version}]
        """
        if not self.targets:
            return []

        if not check_binary("nmap"):
            self.error = "nmap is not installed. Run: sudo pacman -S nmap"
            return []

        self.results = []
        self.findings = []
        
        # Chunk targets into batches of 5
        for i in range(0, len(self.targets), 5):
            batch = self.targets[i:i + 5]
            batch_results = await self._scan_batch(batch)
            self.results.extend(batch_results)
            
            # Map results to Finding objects for HiveRecon database compatibility
            for res in batch_results:
                finding = Finding(
                    agent_type=self.agent_type,
                    finding_type="open_port",
                    severity=self._get_severity(res["port"]),
                    title=f"Open port {res['port']} on {res['host']}",
                    description=f"Service: {res['service']}, Version: {res['version']}",
                    evidence=res,
                    location=f"{res['host']}:{res['port']}",
                )
                self.findings.append(finding)

        return self.results

    async def _scan_batch(self, batch: list[str]) -> list[dict[str, Any]]:
        """Run nmap on a batch of targets with a per-host timeout (120s per host)."""
        # 120s timeout per host in the batch
        timeout = 120 * len(batch)
        cmd = self.get_command(batch)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                if proc.returncode is None:
                    try:
                        proc.kill()
                        await proc.wait()
                    except ProcessLookupError:
                        pass
                self.error = f"Nmap scan timed out for batch: {', '.join(batch)}"
                return []

            if stdout:
                return self._parse_nmap_xml(stdout.decode())
            else:
                if stderr:
                    self.error = stderr.decode()
                return []
        except Exception as e:
            self.error = str(e)
            return []

    def _parse_nmap_xml(self, xml_data: str) -> list[dict[str, Any]]:
        """Parse nmap XML output to extract host, port, service, version, state."""
        batch_findings = []
        if not xml_data.strip():
            return batch_findings
            
        try:
            root = ET.fromstring(xml_data)
            for host in root.findall(".//host"):
                # Extract host (prefer hostname, fallback to IP)
                host_val = "unknown"
                addr_node = host.find("address")
                if addr_node is not None:
                    host_val = addr_node.get("addr", "unknown")
                
                # Check for hostnames in the XML
                hostname_node = host.find(".//hostname")
                if hostname_node is not None:
                    name = hostname_node.get("name")
                    if name:
                        host_val = name

                ports = host.find("ports")
                if ports is not None:
                    for port in ports.findall("port"):
                        # Extract state and ensure it's open
                        state_node = port.find("state")
                        state = state_node.get("state") if state_node is not None else "unknown"
                        
                        if state == "open":
                            port_id = port.get("portid")
                            
                            service_node = port.find("service")
                            service_name = "unknown"
                            version_info = ""
                            
                            if service_node is not None:
                                service_name = service_node.get("name", "unknown")
                                product = service_node.get("product", "")
                                version = service_node.get("version", "")
                                if product:
                                    version_info = f"{product} {version}".strip()
                                else:
                                    version_info = version

                            batch_findings.append({
                                "host": host_val,
                                "port": port_id,
                                "service": service_name,
                                "version": version_info
                            })
        except Exception:
            # Silently handle parsing errors for robustness
            pass
        return batch_findings

    def _get_severity(self, port: str) -> FindingSeverity:
        """Assign severity levels to specific common ports."""
        try:
            p = int(port)
            if p in [21, 22, 23, 3389]:
                return FindingSeverity.LOW
            if p in [1433, 3306, 5432, 27017]:
                return FindingSeverity.MEDIUM
        except ValueError:
            pass
        return FindingSeverity.INFO

    def parse_output(self) -> list[Finding]:
        """Required for BaseAgent compatibility. Returns findings from last execute."""
        return self.findings


class EndpointDiscoveryAgent(BaseAgent):
    """Endpoint discovery agent using katana/ffuf."""

    agent_type = AgentType.ENDPOINT

    def __init__(self, targets: list[str] | list[dict[str, Any]] | str, config: Optional[dict] = None):
        """
        Initialize with targets. 
        Can be a list of host strings, list of dicts (from PortScanAgent), or single host string.
        """
        if isinstance(targets, str):
            self.targets = [targets]
        elif isinstance(targets, list) and targets and isinstance(targets[0], dict):
            # Extract hosts from port scan results if dicts are provided
            self.targets = list(dict.fromkeys([t.get("host") for t in targets if t.get("host")]))
        else:
            self.targets = targets
            
        rep_target = self.targets[0] if self.targets else "multiple-targets"
        super().__init__(rep_target, config)
        self.tool = self.config.get("tool", "auto")  # auto, katana, or ffuf
        self.wordlist = self.config.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        self.all_urls: list[str] = []

    def get_command(self, target: str) -> list:
        """Get endpoint discovery command for a specific target."""
        if self.tool == "ffuf":
            return ["ffuf", "-u", f"https://{target}/FUZZ",
                    "-w", self.wordlist, "-o", "stdout", "-of", "json"]
        # katana v2+ does not support -json; output is plain-text URLs
        return ["katana", "-u", f"https://{target}", "-jc", "-silent"]

    async def execute(self) -> list[str]:
        """Run endpoint discovery on all targets. Returns list of discovered URLs."""
        if not self.targets:
            return []
            
        try:
            # Auto-detect tools
            if self.tool == "auto":
                if check_binary("katana"):
                    self.tool = "katana"
                elif check_binary("ffuf"):
                    self.tool = "ffuf"
                else:
                    self.error = "Neither katana nor ffuf is installed."
                    return []
            elif not check_binary(self.tool):
                self.error = f"{self.tool} is not installed."
                return []

            self.all_urls = []
            self.findings = []
            
            # Process targets sequentially or in small batches
            for target in self.targets:
                proc = await asyncio.create_subprocess_exec(
                    *self.get_command(target),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
                    if stdout:
                        output = stdout.decode()
                        target_findings = self._parse_target_output(output)
                        self.findings.extend(target_findings)
                        for f in target_findings:
                            if f.finding_type == "endpoint" and f.location:
                                self.all_urls.append(f.location)
                except asyncio.TimeoutError:
                    if proc.returncode is None:
                        try:
                            proc.kill()
                            await proc.wait()
                        except ProcessLookupError:
                            pass
                    continue
            
            return list(set(self.all_urls))

        except Exception as e:
            self.error = str(e)
            return []
    
    def _parse_target_output(self, output: str) -> list[Finding]:
        """Parse tool output for a single target."""
        findings = []
        if not output:
            return findings

        if self.tool == "katana":
            for line in output.strip().split("\n"):
                if not line:
                    continue
                try:
                    # Try JSON parsing first (legacy katana)
                    data = json.loads(line)
                    url = data.get("endpoint", data.get("request", {}).get("url", ""))
                    if url:
                        findings.append(Finding(
                            agent_type=self.agent_type,
                            finding_type="endpoint",
                            severity=FindingSeverity.INFO,
                            title=f"Endpoint discovered",
                            description=f"Discovered endpoint during crawling",
                            evidence=data,
                            location=url,
                        ))
                except json.JSONDecodeError:
                    # Newer katana outputs plain URLs, one per line
                    url = line.strip()
                    if url and (url.startswith("http://") or url.startswith("https://")):
                        findings.append(Finding(
                            agent_type=self.agent_type,
                            finding_type="endpoint",
                            severity=FindingSeverity.INFO,
                            title=f"Endpoint discovered",
                            description=f"Discovered endpoint during crawling",
                            location=url,
                        ))
        else:
            try:
                data = json.loads(output)
                for result in data.get("results", []):
                    url = result.get("url", "")
                    status = result.get("status", 0)
                    if url and status:
                        findings.append(Finding(
                            agent_type=self.agent_type,
                            finding_type="endpoint",
                            severity=FindingSeverity.INFO,
                            title=f"Endpoint discovered (HTTP {status})",
                            description=f"Discovered endpoint with status {status}",
                            evidence=result,
                            location=url,
                        ))
            except json.JSONDecodeError:
                pass
        return findings

    def parse_output(self) -> list[Finding]:
        return self.findings


class VulnerabilityScanAgent(BaseAgent):
    """Vulnerability scanning agent using nuclei."""

    agent_type = AgentType.VULNERABILITY

    def __init__(self, targets: list[str] | str, config: Optional[dict] = None):
        """Initialize with a list of URLs or a single URL string."""
        if isinstance(targets, str):
            self.targets = [targets]
        else:
            self.targets = targets
            
        rep_target = self.targets[0] if self.targets else "multiple-urls"
        super().__init__(rep_target, config)

    def get_command(self) -> list:
        """Get nuclei command as list for subprocess."""
        cmd = ["nuclei", "-json", "-silent"]
        
        # Add targets
        for t in self.targets:
            cmd.extend(["-u", t])
            
        templates = self.config.get("templates", "")
        severity_filter = self.config.get("severity_filter", "")
        if templates:
            cmd += ["-t", templates]
        if severity_filter:
            cmd += ["-severity", severity_filter]
        return cmd

    async def execute(self) -> bool:
        """Run vulnerability scan on all targets."""
        if not self.targets:
            return True
            
        try:
            if not check_binary("nuclei"):
                self.error = "nuclei is not installed."
                return False
                
            proc = await asyncio.create_subprocess_exec(
                *self.get_command(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                # Nuclei can take a while for many targets
                timeout = max(300, 60 * len(self.targets))
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                if proc.returncode is None:
                    try:
                        proc.kill()
                        await proc.wait()
                    except ProcessLookupError:
                        pass
                self.error = "Vulnerability scan timed out"
                return False

            if stdout:
                self.output = stdout.decode()
                self.findings = self.parse_output()
                return True
            else:
                if stderr:
                    self.error = stderr.decode()
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
                    
                    findings.append(Finding(
                        agent_type=self.agent_type,
                        finding_type="vulnerability",
                        severity=severity,
                        title=data.get("info", {}).get("name", "Unknown vulnerability"),
                        description=data.get("info", {}).get("description", ""),
                        evidence=data,
                        location=data.get("host", "") + data.get("matched-at", ""),
                    ))
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
                    proc = await asyncio.create_subprocess_exec(
                        *self.get_command(scheme),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                    if stdout and b"HTTP/" in stdout:
                        self.output = stdout.decode()
                        self.findings = self.parse_output()
                        return True
                except asyncio.TimeoutError:
                    continue

            self.error = "Both HTTPS and HTTP connection attempts timed out"
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
