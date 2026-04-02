"""Hive Mind AI Coordinator - LangChain-based agent orchestration."""

import asyncio
import fnmatch
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from hiverecon.agents.recon_agents import AgentType
from hiverecon.config import get_config
from hiverecon.database import (
    AgentRun,
    Finding,
    FindingSeverity,
    Scan,
    ScanStatus,
    Target,
)
from hiverecon.agents.recon_agents import (
    SubdomainAgent,
    PortScanAgent,
    EndpointDiscoveryAgent,
    VulnerabilityScanAgent,
    MCPServerAgent,
)
from hiverecon.core.event_bus import event_bus

logger = logging.getLogger(__name__)


class HiveMindCoordinator:
    """
    Central AI coordinator that orchestrates recon agents.
    
    Responsibilities:
    - Validate targets against scope rules
    - Launch and monitor parallel recon agents
    - Correlate findings across tools
    - Prioritize high-value targets
    - Enforce legal boundaries
    """
    
    def __init__(
        self,
        scan_id: Optional[str] = None,
        session=None,
        config=None,
    ):
        self.scan_id = scan_id
        self.session = session
        self.config = config or get_config()
        
        # Initialize Ollama LLM
        self.llm = ChatOllama(
            model=self.config.ai.model,
            base_url=self.config.ai.base_url,
            temperature=self.config.ai.temperature,
        )
        
        # System prompt for the hive mind
        self.system_prompt = """You are HiveRecon, an AI coordinator for bug bounty reconnaissance.

Your role:
1. Validate targets against scope rules (LEGAL FIRST - never scan out-of-scope)
2. Orchestrate recon agents efficiently
3. Correlate findings to reduce false positives
4. Prioritize high-value targets
5. Provide educational explanations for findings

        Always prioritize legal compliance and responsible disclosure."""

    @staticmethod
    def _normalize_target(value: str) -> str:
        """Normalize targets to a comparable hostname."""
        if not value:
            return ""

        candidate = value.strip()
        if "://" not in candidate:
            candidate = f"//{candidate}"

        parsed = urlparse(candidate)
        host = parsed.hostname or parsed.path.split("/")[0]
        return host.split(":")[0].rstrip(".").lower()

    @classmethod
    def _matches_scope_pattern(cls, candidate: str, pattern: str) -> bool:
        """Match a target against a literal or wildcard scope pattern."""
        normalized_candidate = cls._normalize_target(candidate)
        normalized_pattern = cls._normalize_target(pattern)

        if not normalized_candidate or not normalized_pattern:
            return False

        if fnmatch.fnmatch(normalized_candidate, normalized_pattern):
            return True

        if normalized_pattern.startswith("*."):
            suffix = normalized_pattern[2:]
            return (
                normalized_candidate == suffix
                or normalized_candidate.endswith(f".{suffix}")
            )

        return normalized_candidate == normalized_pattern

    @classmethod
    def _is_target_in_scope(cls, target: str, scope_config: Optional[dict]) -> bool:
        """Check a target against the supplied scope configuration."""
        if not isinstance(scope_config, dict):
            return True

        source_scope = (
            scope_config.get("scope_config")
            if isinstance(scope_config.get("scope_config"), dict)
            else scope_config
        )
        in_scope = source_scope.get("in_domains") or source_scope.get("in_scope") or []
        out_scope = source_scope.get("out_domains") or source_scope.get("out_scope") or []

        in_scope_patterns = [
            item for item in in_scope if isinstance(item, str) and item.strip()
        ]
        out_scope_patterns = [
            item for item in out_scope if isinstance(item, str) and item.strip()
        ]

        if any(cls._matches_scope_pattern(target, pattern) for pattern in out_scope_patterns):
            return False

        if in_scope_patterns:
            return any(
                cls._matches_scope_pattern(target, pattern)
                for pattern in in_scope_patterns
            )

        return True

    async def ai_prioritize_subdomains(self, subdomains: list[str]) -> dict:
        """
        Categorize discovered subdomains by attack surface priority using keyword matching.

        Categories:
        - high_priority: admin, api, dev, staging, vpn, mail, jenkins, jira, grafana, kibana, internal, test, beta
        - medium_priority: everything else interesting
        - low_priority: cdn, static, assets, img, fonts, ns records

        Returns dict with three keys, each containing a list of subdomain strings.
        """
        HIGH_KEYWORDS = [
            'api', 'admin', 'dev', 'staging', 'stage', 'vpn', 'mail',
            'smtp', 'jenkins', 'jira', 'gitlab', 'grafana', 'kibana',
            'internal', 'test', 'beta', 'dashboard', 'portal', 'manage',
            'console', 'auth', 'login', 'sso', 'oauth', 'upload', 'files',
            'backend', 'app', 'secure', 'private', 'corp', 'intranet'
        ]
        LOW_KEYWORDS = [
            'mta-sts', 'autodiscover', 'fonts', 'assets', 'static',
            'img', 'images', 'cdn', 'a.ns', 'b.ns', 'ns1', 'ns2',
            'mail._domainkey', '_dmarc', 'forwarding'
        ]
        
        high, medium, low = [], [], []
        
        for subdomain in subdomains:
            sub_lower = subdomain.lower()
            if any(kw in sub_lower for kw in LOW_KEYWORDS):
                low.append(subdomain)
            elif any(kw in sub_lower for kw in HIGH_KEYWORDS):
                high.append(subdomain)
            else:
                medium.append(subdomain)
        
        logger.info(
            f'Prioritization: {len(high)} high, '
            f'{len(medium)} medium, {len(low)} low'
        )
        return {'high_priority': high, 'medium_priority': medium, 'low_priority': low}

    async def ai_select_scan_targets(self, port_results: list[dict]) -> list[str]:
        """
        Use AI to select which hosts should get deep endpoint discovery based on port scan findings.

        Prioritizes hosts with ports 80, 443, 8080, 8443, 3000, 8000 open.
        Returns a list of host strings.
        """
        if not port_results:
            return []

        # Extract unique hosts and their open ports
        host_ports: dict[str, list[str]] = {}
        for res in port_results:
            host = res.get("host")
            port = res.get("port")
            if host and port:
                if host not in host_ports:
                    host_ports[host] = []
                host_ports[host].append(str(port))

        if not host_ports:
            return []

        prompt = f"""
        Based on these port scan findings, which hosts should get deep endpoint discovery?

        {json.dumps(host_ports, indent=2)}

        Prioritize hosts with these ports open: 80, 443, 8080, 8443, 3000, 8000
        Also consider hosts with other interesting ports like: 8081, 8000, 5000, 9000, 9200, 27017

        Respond with a JSON list of host strings that should be scanned for endpoints.
        Example: ["192.168.1.1", "api.example.com"]
        """

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])

            result = json.loads(response.content.strip())

            if isinstance(result, list):
                return [str(host) for host in result if host]
            return list(host_ports.keys())

        except Exception:
            # Fallback: return all unique hosts
            return list(host_ports.keys())

    async def ai_select_vuln_targets(self, urls: list[str]) -> list[str]:
        """
        Use AI to select which endpoints are highest priority for vulnerability scanning.

        Looks for: admin panels, login pages, API endpoints, GraphQL, file upload endpoints,
        endpoints with parameters.

        Returns a list of URLs.
        """
        if not urls:
            return []

        prompt = f"""
        Based on these discovered endpoints, which are highest priority for vulnerability scanning?

        {json.dumps(urls, indent=2)}

        Prioritize:
        - Admin panels (/admin, /dashboard, /panel)
        - Login pages (/login, /signin, /auth)
        - API endpoints (/api/, /graphql, /rest/)
        - File upload endpoints (/upload, /files, /attachments)
        - Endpoints with parameters (?id=, ?user=, ?file=, etc.)
        - Configuration endpoints (/config, /settings, /.env)
        - Debug/dev endpoints (/debug, /dev, /test)

        Respond with a JSON list of URLs to scan for vulnerabilities.
        Example: ["https://example.com/admin", "https://api.example.com/v1/users"]
        """

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])

            result = json.loads(response.content.strip())

            if isinstance(result, list):
                return [str(url) for url in result if url]
            return urls

        except Exception:
            # Fallback: return all endpoints
            return urls

    async def validate_scope(self, targets: list[dict]) -> list[Target]:
        """
        Validate targets against scope rules using AI.
        
        Returns validated in-scope targets.
        """
        validated_targets = []
        
        for target_data in targets:
            # Use AI to validate scope
            prompt = f"""
            Validate if this target is in scope for bug bounty hunting:
            
            Target: {target_data.get('value')}
            Type: {target_data.get('type')}
            Scope Rules: {json.dumps(target_data.get('scope_rules', {}))}
            
            Respond with JSON:
            {{
                "in_scope": true/false,
                "reason": "explanation",
                "risk_level": "low/medium/high"
            }}
            """
            
            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt)
                ])
                
                # Parse AI response
                analysis = json.loads(response.content.strip())
                
                if analysis.get("in_scope", False):
                    target = Target(
                        scan_id=self.scan_id,
                        target_type=target_data.get("type", "domain"),
                        target_value=target_data.get("value"),
                        in_scope=True,
                        validated=True,
                        validation_notes=analysis.get("reason", ""),
                    )
                    validated_targets.append(target)
            except Exception as e:
                # Log error but continue
                target = Target(
                    scan_id=self.scan_id,
                    target_type=target_data.get("type", "domain"),
                    target_value=target_data.get("value"),
                    in_scope=False,
                    validated=True,
                    validation_notes=f"Validation error: {str(e)}",
                )
                validated_targets.append(target)
        
        return validated_targets

    async def launch_agents(self) -> list[AgentRun]:
        """Launch all recon agents in parallel."""
        
        agents = [
            AgentType.SUBDOMAIN,
            AgentType.PORT_SCAN,
            AgentType.ENDPOINT,
            AgentType.VULNERABILITY,
            AgentType.MCP,
        ]
        
        agent_runs = []
        
        for agent_type in agents:
            agent_run = AgentRun(
                scan_id=self.scan_id,
                agent_type=agent_type,
                status=ScanStatus.PENDING,
            )
            agent_runs.append(agent_run)
        
        # Execute agents with concurrency limit
        semaphore = asyncio.Semaphore(self.config.scan.max_concurrent_agents)
        
        async def run_agent(agent_run: AgentRun):
            async with semaphore:
                await self._execute_agent(agent_run)
        
        tasks = [run_agent(agent) for agent in agent_runs]
        await asyncio.gather(*tasks, return_exceptions=True)

        return agent_runs

    async def run_scan(
        self,
        target: str,
        scan_id: Optional[str] = None,
        scope_config: Optional[dict] = None,
    ) -> list[Finding]:
        """
        Orchestrate the full recon pipeline on a target.
        """
        self.scan_id = scan_id or self.scan_id
        agent_config = scope_config or {}
        all_findings: list[Finding] = []

        normalized_target = self._normalize_target(target)
        if not normalized_target:
            raise ValueError("Invalid target")

        if not self._is_target_in_scope(normalized_target, scope_config):
            raise ValueError("Target is out of scope")

        async def save_agent_results(agent_type: AgentType, agent_findings: list[Finding]):
            """Helper to save agent findings to DB immediately."""
            if self.session:
                for finding in agent_findings:
                    finding.scan_id = self.scan_id
                    self.session.add(finding)
                await self.session.commit()

        # Step 1: Subdomain Discovery
        await event_bus.publish(self.scan_id, {
            "event": "progress", "stage": "subdomain_enum", "pct": 10,
            "message": f"Starting subdomain discovery on {normalized_target}", "findings_count": len(all_findings)
        })
        print(f"[*] Starting Subdomain Discovery on {normalized_target}...")
        subdomain_agent = SubdomainAgent(normalized_target, agent_config)
        if await subdomain_agent.execute():
            all_findings.extend(subdomain_agent.findings)
            await save_agent_results(AgentType.SUBDOMAIN, subdomain_agent.findings)
            print(f"[+] Discovered {len(subdomain_agent.findings)} subdomains.")
        else:
            print(f"[-] Subdomain discovery failed: {subdomain_agent.error}")

        # Extract discovered subdomains
        discovered_subdomains = list(set([
            f.location for f in subdomain_agent.findings 
            if f.finding_type == "subdomain" and f.location
        ]))
        if not discovered_subdomains:
            discovered_subdomains = [normalized_target]

        # AI Prioritization
        print(f"[*] AI Prioritizing {len(discovered_subdomains)} subdomains...")
        priority_map = await self.ai_prioritize_subdomains(discovered_subdomains)
        high_priority = priority_map.get("high_priority", [])
        medium_priority = priority_map.get("medium_priority", [])
        
        # Combine high and medium for scanning
        targets_to_scan = list(dict.fromkeys(high_priority + medium_priority))
        if not targets_to_scan:
            targets_to_scan = discovered_subdomains[:10] # Fallback
            
        # Step 2: Port Scanning
        await event_bus.publish(self.scan_id, {
            "event": "progress", "stage": "port_scan", "pct": 30,
            "message": f"Starting port scan on {len(targets_to_scan)} targets", "findings_count": len(all_findings)
        })
        print(f"[*] Starting Port Scan on {len(targets_to_scan)} targets...")
        port_agent = PortScanAgent(targets=targets_to_scan, config=agent_config)
        port_results = await port_agent.execute()
        all_findings.extend(port_agent.findings)
        await save_agent_results(AgentType.PORT_SCAN, port_agent.findings)
        print(f"[+] Port scan complete. Found {len(port_results)} open ports.")

        # Step 3: AI Target Selection for Endpoint Discovery
        print("[*] AI selecting targets for endpoint discovery...")
        selected_hosts = await self.ai_select_scan_targets(port_results)
        
        # Filter port results to only those selected by AI
        filtered_scan_targets = [
            res for res in port_results 
            if res.get("host") in selected_hosts
        ]
        if not filtered_scan_targets and port_results:
            filtered_scan_targets = port_results[:5] # Fallback
            
        print(f"[+] AI selected {len(filtered_scan_targets)} targets for deep discovery.")

        # Step 4: Endpoint Discovery
        await event_bus.publish(self.scan_id, {
            "event": "progress", "stage": "endpoint_discovery", "pct": 50,
            "message": f"Starting endpoint discovery on {len(filtered_scan_targets)} targets", "findings_count": len(all_findings)
        })
        print(f"[*] Starting Endpoint Discovery on selected targets...")
        endpoint_agent = EndpointDiscoveryAgent(targets=filtered_scan_targets, config=agent_config)
        discovered_urls = await endpoint_agent.execute()
        all_findings.extend(endpoint_agent.findings)
        await save_agent_results(AgentType.ENDPOINT, endpoint_agent.findings)
        print(f"[+] Discovered {len(discovered_urls)} unique URLs.")

        # Step 5: AI Vulnerability Target Selection
        print("[*] AI selecting high-value URLs for vulnerability scanning...")
        selected_urls = await self.ai_select_vuln_targets(discovered_urls)
        
        # Filter discovered URLs to only those selected by AI
        filtered_urls = [url for url in discovered_urls if url in selected_urls]
        if not filtered_urls and discovered_urls:
            filtered_urls = discovered_urls[:5] # Fallback
            
        print(f"[+] AI selected {len(filtered_urls)} URLs for nuclei scanning.")

        # Step 6: Vulnerability Scanning
        await event_bus.publish(self.scan_id, {
            "event": "progress", "stage": "vuln_scan", "pct": 70,
            "message": f"Starting vulnerability scan on {len(filtered_urls)} URLs", "findings_count": len(all_findings)
        })
        if filtered_urls:
            print(f"[*] Starting Vulnerability Scan with Nuclei on {len(filtered_urls)} URLs...")
            vuln_agent = VulnerabilityScanAgent(targets=filtered_urls, config=agent_config)
            if await vuln_agent.execute():
                all_findings.extend(vuln_agent.findings)
                await save_agent_results(AgentType.VULNERABILITY, vuln_agent.findings)
                print(f"[+] Vulnerability scan complete. Found {len(vuln_agent.findings)} issues.")
            else:
                print(f"[-] Vulnerability scan failed: {vuln_agent.error}")
        else:
            print("[!] No URLs selected for vulnerability scanning.")

        # Final Correlation and Enrichment
        await event_bus.publish(self.scan_id, {
            "event": "progress", "stage": "correlation", "pct": 90,
            "message": "Correlating findings and generating insights", "findings_count": len(all_findings)
        })
        print("[*] Correlating findings and generating educational content...")
        all_findings = await self.correlate_findings(all_findings)
        for finding in all_findings:
            await self.generate_educational_content(finding)
        
        # Step 7: Run MCPServerAgent on the original target
        try:
            mcp_agent = MCPServerAgent(normalized_target, agent_config)
            if await mcp_agent.execute():
                all_findings.extend(mcp_agent.findings)
                await save_agent_results(AgentType.MCP, mcp_agent.findings)
        except Exception as e:
            print(f"[-] MCP agent failed: {str(e)}")

        await event_bus.publish(self.scan_id, {
            "event": "complete",
            "summary": {
                "total_findings": len(all_findings),
                "target": normalized_target,
                "completed_at": datetime.utcnow().isoformat()
            }
        })
        await event_bus.close_scan(self.scan_id)

        print(f"[***] Scan Complete! Total Findings: {len(all_findings)}")
        return all_findings

    async def _execute_agent(self, agent_run: AgentRun) -> None:
        """Execute a single recon agent."""
        
        agent_run.status = ScanStatus.RUNNING
        agent_run.started_at = datetime.utcnow()
        
        try:
            # Get scan targets
            scan = await self.session.get(Scan, self.scan_id)
            targets = [t.target_value for t in scan.targets if t.in_scope]
            
            if not targets:
                agent_run.status = ScanStatus.COMPLETED
                agent_run.error_message = "No in-scope targets to scan"
                return
            
            # Build command based on agent type
            command = self._build_agent_command(agent_run.agent_type, targets)
            agent_run.command = command
            
            # Execute command (placeholder - actual implementation in agents module)
            # This will be replaced with actual agent execution
            output = await self._run_command(command)
            agent_run.output = output
            agent_run.status = ScanStatus.COMPLETED
            
        except Exception as e:
            agent_run.status = ScanStatus.FAILED
            agent_run.error_message = str(e)
        
        finally:
            agent_run.completed_at = datetime.utcnow()

    def _build_agent_command(self, agent_type: AgentType, targets: list[str]) -> str:
        """Build the command for a specific agent type."""
        
        target = targets[0] if targets else "example.com"
        
        commands = {
            AgentType.SUBDOMAIN: f"subfinder -d {target} -silent",
            AgentType.PORT_SCAN: f"nmap -sV -sC -oN - {target}",
            AgentType.ENDPOINT: f"katana -u https://{target} -jc -silent",
            AgentType.VULNERABILITY: f"nuclei -u https://{target} -json",
            AgentType.MCP: f"mcp-client --target {target}",
        }
        
        return commands.get(agent_type, "echo 'Unknown agent type'")

    async def _run_command(self, command: str) -> str:
        """Run a shell command and return output."""
        # Placeholder - actual implementation will use asyncio.create_subprocess_shell
        return f"Command executed: {command}"

    async def correlate_findings(self, findings: list[Finding]) -> list[Finding]:
        """
        Use AI to correlate findings across tools.
        
        - Reduce false positives
        - Prioritize high-value findings
        - Group related findings
        """
        
        if not findings:
            return []
        
        # Prepare findings for AI analysis
        findings_summary = [
            {
                "type": f.finding_type,
                "title": f.title,
                "location": f.location,
                "severity": f.severity.value,
            }
            for f in findings
        ]
        
        prompt = f"""
        Analyze and correlate these security findings:
        
        {json.dumps(findings_summary, indent=2)}
        
        For each finding, provide:
        1. Is this likely a false positive? (yes/no with reason)
        2. Priority score (1-10)
        3. Related findings that should be grouped
        4. Recommended next steps
        
        Respond with JSON array of analyses.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])
            
            analyses = json.loads(response.content.strip())
            
            # Apply AI analysis to findings
            for i, finding in enumerate(findings):
                if i < len(analyses):
                    finding.ai_analysis = analyses[i]
            
            return findings
            
        except Exception as e:
            # Return original findings if correlation fails
            return findings

    async def generate_educational_content(self, finding: Finding) -> None:
        """
        Generate beginner-friendly educational content for a finding.
        
        Includes:
        - What this vulnerability means
        - Why it matters
        - How to reproduce it
        - How to write a good bug bounty report
        """
        
        prompt = f"""
        Explain this security finding for a beginner bug bounty hunter:
        
        Type: {finding.finding_type}
        Title: {finding.title}
        Location: {finding.location}
        Description: {finding.description}
        
        Provide:
        1. **What is this?** (simple explanation)
        2. **Why does it matter?** (impact)
        3. **How to reproduce?** (step-by-step)
        4. **Severity justification** (why this severity level)
        5. **Report writing tips** (how to document for bug bounty)
        
        Keep it educational and encouraging for beginners.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])
            
            finding.educational_content = response.content
            
        except Exception as e:
            finding.educational_content = f"Error generating educational content: {str(e)}"
