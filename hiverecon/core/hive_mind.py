"""Hive Mind AI Coordinator - LangChain-based agent orchestration."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from hiverecon.config import get_config
from hiverecon.database import (
    AgentRun,
    AgentType,
    Finding,
    FindingSeverity,
    Scan,
    ScanStatus,
    Target,
)


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
    
    def __init__(self, scan_id: str, session):
        self.scan_id = scan_id
        self.session = session
        self.config = get_config()
        
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
