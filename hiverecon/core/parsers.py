"""
Unified output parsers for recon tools.

Handles version differences and provides consistent output format.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class ParsedResult:
    """Standardized parsed result from any recon tool."""
    
    finding_type: str
    value: str
    severity: str = "info"
    title: str = ""
    description: str = ""
    metadata: dict[str, Any] = None
    raw_output: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "finding_type": self.finding_type,
            "value": self.value,
            "severity": self.severity,
            "title": self.title or f"{self.finding_type}: {self.value}",
            "description": self.description,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class BaseParser(ABC):
    """Base class for tool output parsers."""
    
    tool_name: str
    
    @abstractmethod
    def parse(self, output: str) -> list[ParsedResult]:
        """Parse tool output into standardized results."""
        pass
    
    def parse_file(self, filepath: str) -> list[ParsedResult]:
        """Parse output from a file."""
        with open(filepath) as f:
            return self.parse(f.read())


class SubfinderParser(BaseParser):
    """Parser for subfinder output (JSON and text)."""
    
    tool_name = "subfinder"
    
    def parse(self, output: str) -> list[ParsedResult]:
        results = []
        
        if not output.strip():
            return results
        
        # Try JSON parsing first (newer versions support -json flag)
        lines = output.strip().split("\n")
        is_json = False
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                is_json = True
                
                # Handle different subfinder JSON formats
                host = data.get("host", data.get("domain", ""))
                if host:
                    results.append(ParsedResult(
                        finding_type="subdomain",
                        value=host,
                        severity="info",
                        title=f"Subdomain: {host}",
                        description="Discovered via subfinder enumeration",
                        metadata={
                            "source": "subfinder",
                            "resolver": data.get("resolver", ""),
                            "ip": data.get("ip", ""),
                        },
                        raw_output=line,
                    ))
            except json.JSONDecodeError:
                # Not JSON, treat as plain text
                break
        
        # If not JSON, parse as plain text (one subdomain per line)
        if not is_json:
            for line in lines:
                subdomain = line.strip()
                if subdomain and self._is_valid_domain(subdomain):
                    results.append(ParsedResult(
                        finding_type="subdomain",
                        value=subdomain,
                        severity="info",
                        title=f"Subdomain: {subdomain}",
                        description="Discovered via subfinder enumeration",
                        metadata={"source": "subfinder", "format": "text"},
                        raw_output=line,
                    ))
        
        return results
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Basic domain validation."""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))


class AmassParser(BaseParser):
    """Parser for amass output."""
    
    tool_name = "amass"
    
    def parse(self, output: str) -> list[ParsedResult]:
        results = []
        
        if not output.strip():
            return results
        
        # Amass IPv4 output format: IP,STATUS,DOMAIN,SOURCE
        # Simple text output: one domain per line
        lines = output.strip().split("\n")
        
        for line in lines:
            parts = line.split(",")
            
            if len(parts) >= 3:
                # CSV format
                domain = parts[2].strip()
                source = parts[3].strip() if len(parts) > 3 else "amass"
            else:
                # Plain text format
                domain = line.strip()
                source = "amass"
            
            if domain and self._is_valid_domain(domain):
                results.append(ParsedResult(
                    finding_type="subdomain",
                    value=domain,
                    severity="info",
                    title=f"Subdomain: {domain}",
                    description="Discovered via amass enumeration",
                    metadata={"source": "amass", "format": "text"},
                    raw_output=line,
                ))
        
        return results
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Basic domain validation."""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))


class NmapParser(BaseParser):
    """Parser for nmap output (normal format)."""
    
    tool_name = "nmap"
    
    # Common ports and their risk levels
    PORT_RISK = {
        "21": ("FTP", "low"),
        "22": ("SSH", "low"),
        "23": ("Telnet", "medium"),  # Insecure protocol
        "25": ("SMTP", "low"),
        "53": ("DNS", "low"),
        "80": ("HTTP", "low"),
        "110": ("POP3", "low"),
        "135": ("MS-RPC", "medium"),
        "139": ("NetBIOS", "medium"),
        "143": ("IMAP", "low"),
        "443": ("HTTPS", "low"),
        "445": ("SMB", "medium"),
        "993": ("IMAPS", "low"),
        "995": ("POP3S", "low"),
        "1433": ("MSSQL", "high"),  # Database exposed
        "1521": ("Oracle", "high"),
        "3306": ("MySQL", "high"),
        "3389": ("RDP", "medium"),
        "5432": ("PostgreSQL", "high"),
        "5900": ("VNC", "medium"),
        "6379": ("Redis", "high"),
        "8080": ("HTTP-Proxy", "low"),
        "27017": ("MongoDB", "high"),
    }
    
    def parse(self, output: str) -> list[ParsedResult]:
        results = []
        
        if not output.strip():
            return results
        
        current_host = ""
        in_ports_section = False
        
        for line in output.split("\n"):
            line = line.strip()
            
            # Detect host
            if line.startswith("Nmap scan report for"):
                current_host = line.replace("Nmap scan report for", "").strip()
                in_ports_section = False
            
            # Detect ports section
            if "PORT" in line and "STATE" in line:
                in_ports_section = True
                continue
            
            # Parse port lines
            if in_ports_section and "/" in line:
                parts = line.split()
                if len(parts) >= 3:
                    port_info = parts[0]  # e.g., "22/tcp"
                    state = parts[1]       # e.g., "open"
                    service = " ".join(parts[2:]) if len(parts) > 2 else "unknown"
                    
                    if state == "open":
                        port_num = port_info.split("/")[0]
                        service_name, severity = self.PORT_RISK.get(
                            port_num, (service, "info")
                        )
                        
                        results.append(ParsedResult(
                            finding_type="open_port",
                            value=f"{current_host}:{port_num}",
                            severity=severity,
                            title=f"Open port {port_num} ({service_name})",
                            description=f"Service: {service}",
                            metadata={
                                "host": current_host,
                                "port": port_num,
                                "service": service_name,
                                "service_detail": service,
                            },
                            raw_output=line,
                        ))
        
        return results


class KatanaParser(BaseParser):
    """Parser for katana output."""
    
    tool_name = "katana"
    
    def parse(self, output: str) -> list[ParsedResult]:
        results = []
        
        if not output.strip():
            return results
        
        lines = output.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                # Katana JSON output
                data = json.loads(line)
                endpoint = data.get("endpoint", data.get("request", {}).get("url", ""))
                
                if endpoint:
                    # Categorize endpoint by type
                    endpoint_type = self._categorize_endpoint(endpoint)
                    
                    results.append(ParsedResult(
                        finding_type="endpoint",
                        value=endpoint,
                        severity="info",
                        title=f"Endpoint discovered: {endpoint_type}",
                        description=f"Discovered via katana crawling",
                        metadata={
                            "source": "katana",
                            "endpoint_type": endpoint_type,
                            "method": data.get("method", "GET"),
                        },
                        raw_output=line,
                    ))
            except json.JSONDecodeError:
                # Plain text output
                if line.startswith("http"):
                    results.append(ParsedResult(
                        finding_type="endpoint",
                        value=line.strip(),
                        severity="info",
                        title="Endpoint discovered",
                        description="Discovered via katana crawling",
                        metadata={"source": "katana", "format": "text"},
                        raw_output=line,
                    ))
        
        return results
    
    def _categorize_endpoint(self, url: str) -> str:
        """Categorize endpoint by potential sensitivity."""
        url_lower = url.lower()
        
        sensitive_patterns = [
            ("admin", "admin_panel"),
            ("login", "authentication"),
            ("api", "api_endpoint"),
            ("graphql", "graphql_endpoint"),
            (".git", "git_exposure"),
            (".env", "config_exposure"),
            ("backup", "backup_file"),
            ("config", "config_file"),
            ("debug", "debug_endpoint"),
            ("test", "test_endpoint"),
        ]
        
        for pattern, category in sensitive_patterns:
            if pattern in url_lower:
                return category
        
        return "general"


class FfufParser(BaseParser):
    """Parser for ffuf output."""
    
    tool_name = "ffuf"
    
    def parse(self, output: str) -> list[ParsedResult]:
        results = []
        
        if not output.strip():
            return results
        
        try:
            # ffuf JSON output
            data = json.loads(output)
            
            for result in data.get("results", []):
                url = result.get("url", "")
                status = result.get("status", 0)
                length = result.get("length", 0)
                words = result.get("words", 0)
                
                if url:
                    # Categorize by status code
                    severity, category = self._categorize_status(status)
                    
                    results.append(ParsedResult(
                        finding_type="endpoint",
                        value=url,
                        severity=severity,
                        title=f"Endpoint (HTTP {status}) - {category}",
                        description=f"Discovered via ffuf fuzzing",
                        metadata={
                            "source": "ffuf",
                            "status": status,
                            "length": length,
                            "words": words,
                            "category": category,
                        },
                        raw_output=json.dumps(result),
                    ))
        
        except json.JSONDecodeError:
            # Plain text output parsing (less reliable)
            for line in output.strip().split("\n"):
                if line.startswith("http"):
                    results.append(ParsedResult(
                        finding_type="endpoint",
                        value=line.split()[0] if " " in line else line,
                        severity="info",
                        title="Endpoint discovered",
                        description="Discovered via ffuf fuzzing",
                        metadata={"source": "ffuf", "format": "text"},
                        raw_output=line,
                    ))
        
        return results
    
    def _categorize_status(self, status: int) -> tuple[str, str]:
        """Categorize endpoint by HTTP status code."""
        if status in [200, 201, 204]:
            return "low", "success"
        elif status in [301, 302, 307, 308]:
            return "info", "redirect"
        elif status == 401:
            return "medium", "authentication_required"
        elif status == 403:
            return "low", "forbidden"
        elif status == 404:
            return "info", "not_found"
        elif status in [500, 502, 503]:
            return "medium", "server_error"
        else:
            return "info", "other"


class NucleiParser(BaseParser):
    """Parser for nuclei vulnerability scan output."""
    
    tool_name = "nuclei"
    
    SEVERITY_MAP = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "info",
        "unknown": "info",
    }
    
    def parse(self, output: str) -> list[ParsedResult]:
        results = []
        
        if not output.strip():
            return results
        
        lines = output.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                # Nuclei JSON output
                data = json.loads(line)
                
                info = data.get("info", {})
                name = info.get("name", "Unknown vulnerability")
                severity = self.SEVERITY_MAP.get(
                    info.get("severity", "info").lower(),
                    "info"
                )
                description = info.get("description", "")
                
                host = data.get("host", "")
                matched_at = data.get("matched-at", "")
                matched = data.get("matched", "")
                
                results.append(ParsedResult(
                    finding_type="vulnerability",
                    value=f"{host}{matched_at}",
                    severity=severity,
                    title=name,
                    description=description,
                    metadata={
                        "source": "nuclei",
                        "template_id": data.get("template-id", ""),
                        "template_path": data.get("template-path", ""),
                        "type": data.get("type", ""),
                        "host": host,
                        "matched_at": matched_at,
                        "matched": matched,
                        "extracted_results": data.get("extracted-results", []),
                    },
                    raw_output=line,
                ))
            
            except json.JSONDecodeError:
                # Plain text output (less common for nuclei)
                # Format: [severity] vulnerability_name [host]
                match = re.match(
                    r'\[(\w+)\]\s+(\S+)\s+\[(\S+)\]',
                    line
                )
                if match:
                    severity, name, host = match.groups()
                    results.append(ParsedResult(
                        finding_type="vulnerability",
                        value=host,
                        severity=self.SEVERITY_MAP.get(severity.lower(), "info"),
                        title=name,
                        description="Discovered via nuclei scan",
                        metadata={"source": "nuclei", "format": "text"},
                        raw_output=line,
                    ))
        
        return results


# Parser registry
PARSER_REGISTRY = {
    "subfinder": SubfinderParser,
    "amass": AmassParser,
    "nmap": NmapParser,
    "katana": KatanaParser,
    "ffuf": FfufParser,
    "nuclei": NucleiParser,
}


def get_parser(tool_name: str) -> BaseParser:
    """Get parser for a specific tool."""
    parser_class = PARSER_REGISTRY.get(tool_name)
    if not parser_class:
        raise ValueError(f"No parser registered for tool: {tool_name}")
    return parser_class()


def parse_output(tool_name: str, output: str) -> list[ParsedResult]:
    """Parse tool output using the appropriate parser."""
    parser = get_parser(tool_name)
    return parser.parse(output)
