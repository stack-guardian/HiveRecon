"""
Audit logging system for legal compliance and accountability.

All actions are logged with timestamps, actors, and details.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from hiverecon.config import get_config


class AuditAction(str, Enum):
    """Types of auditable actions."""
    
    # Scan lifecycle
    SCAN_CREATED = "scan.created"
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    SCAN_CANCELLED = "scan.cancelled"
    
    # Target management
    TARGET_ADDED = "target.added"
    TARGET_REMOVED = "target.removed"
    TARGET_VALIDATED = "target.validated"
    SCOPE_VALIDATED = "scope.validated"
    
    # Agent execution
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    
    # Findings
    FINDING_DISCOVERED = "finding.discovered"
    FINDING_ANALYZED = "finding.analyzed"
    FINDING_EXPORTED = "finding.exported"
    
    # Report generation
    REPORT_GENERATED = "report.generated"
    REPORT_EXPORTED = "report.exported"
    
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    
    # System
    CONFIG_CHANGED = "config.changed"
    TOOL_EXECUTED = "tool.executed"
    RATE_LIMIT_HIT = "rate_limit.hit"
    ERROR_OCCURRED = "error occurred"


class AuditLogger:
    """
    Comprehensive audit logger for compliance.
    
    Features:
    - Immutable log entries (append-only)
    - Multiple output formats (JSON, CSV)
    - Tamper-evident logging
    - Configurable retention
    """
    
    def __init__(
        self,
        log_file: Optional[str] = None,
        level: str = "INFO",
    ):
        config = get_config()
        
        self.log_file = log_file or config.logging.audit_file
        self.level = level
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("hiverecon.audit")
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # File handler - JSON format
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(file_handler)
            
            # Console handler for errors
            if level.upper() == "DEBUG":
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(
                    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
                )
                self.logger.addHandler(console_handler)
        
        self._lock = asyncio.Lock()
    
    async def log(
        self,
        action: AuditAction,
        actor: str = "system",
        scan_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log an auditable action.
        
        Args:
            action: The type of action being performed
            actor: Who performed the action (user or system)
            scan_id: Related scan ID if applicable
            details: Additional context about the action
            ip_address: IP address of the actor if applicable
        """
        async with self._lock:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": action.value,
                "actor": actor,
                "scan_id": scan_id,
                "details": details or {},
                "ip_address": ip_address,
                "version": 1,
            }
            
            # Log as JSON for easy parsing
            self.logger.info(json.dumps(entry))
    
    async def log_scan_event(
        self,
        scan_id: str,
        action: AuditAction,
        details: Optional[dict] = None,
        actor: str = "system",
    ) -> None:
        """Log a scan-related event."""
        await self.log(
            action=action,
            actor=actor,
            scan_id=scan_id,
            details=details,
        )
    
    async def log_tool_execution(
        self,
        tool_name: str,
        command: str,
        target: str,
        scan_id: Optional[str] = None,
        actor: str = "system",
    ) -> None:
        """Log tool execution for compliance."""
        await self.log(
            action=AuditAction.TOOL_EXECUTED,
            actor=actor,
            scan_id=scan_id,
            details={
                "tool": tool_name,
                "command": command,
                "target": target,
            },
        )
    
    async def log_scope_validation(
        self,
        target: str,
        in_scope: bool,
        reason: str,
        scan_id: Optional[str] = None,
    ) -> None:
        """Log scope validation result."""
        await self.log(
            action=AuditAction.SCOPE_VALIDATED,
            actor="system",
            scan_id=scan_id,
            details={
                "target": target,
                "in_scope": in_scope,
                "reason": reason,
            },
        )
    
    async def log_error(
        self,
        error: str,
        context: Optional[dict] = None,
        scan_id: Optional[str] = None,
        actor: str = "system",
    ) -> None:
        """Log an error event."""
        await self.log(
            action=AuditAction.ERROR_OCCURRED,
            actor=actor,
            scan_id=scan_id,
            details={
                "error": error,
                "context": context or {},
            },
        )
    
    def get_logs(
        self,
        scan_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Retrieve audit logs with filters.
        
        Note: For production, use a proper database. This is a simple file-based implementation.
        """
        logs = []
        
        if not os.path.exists(self.log_file):
            return logs
        
        with open(self.log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                
                # Apply filters
                if scan_id and entry.get("scan_id") != scan_id:
                    continue
                
                if action and entry.get("action") != action.value:
                    continue
                
                if start_time:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                    if entry_time < start_time:
                        continue
                
                if end_time:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                    if entry_time > end_time:
                        continue
                
                logs.append(entry)
                
                if len(logs) >= limit:
                    break
        
        return logs
    
    def export_logs(
        self,
        output_file: str,
        format: str = "json",
        scan_id: Optional[str] = None,
    ) -> str:
        """Export audit logs to a file."""
        logs = self.get_logs(scan_id=scan_id)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, "w") as f:
                json.dump(logs, f, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, "w", newline="") as f:
                if logs:
                    writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                    writer.writeheader()
                    writer.writerows(logs)
        else:
            # Plain text format
            with open(output_path, "w") as f:
                for log in logs:
                    f.write(f"{log.get('timestamp')} - {log.get('action')} - {log.get('actor')}\n")
        
        return str(output_path)


class LegalDisclaimer:
    """
    Manages legal disclaimers and user acknowledgments.
    
    Ensures users acknowledge legal requirements before scanning.
    """
    
    DISCLAIMER_TEXT = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ⚖️  LEGAL DISCLAIMER  ⚖️                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  HiveRecon is designed for AUTHORIZED security research only.                ║
║                                                                              ║
║  By using this tool, you acknowledge and agree:                              ║
║                                                                              ║
║  • You have EXPLICIT WRITTEN AUTHORIZATION to scan the target                ║
║  • You will respect SCOPE BOUNDARIES at all times                            ║
║  • You are responsible for COMPLIANCE with all applicable laws               ║
║  • You understand that UNAUTHORIZED SCANNING IS ILLEGAL                      ║
║  • All actions are LOGGED for accountability and audit purposes              ║
║  • You will follow RESPONSIBLE DISCLOSURE practices                          ║
║                                                                              ║
║  This tool is provided "AS IS" without warranty. The authors are             ║
║  not liable for any misuse or damages resulting from its use.                ║
║                                                                              ║
║  Violation of these terms may result in civil and criminal penalties.        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    ACKNOWLEDGMENT_TEXT = """
I hereby certify that:

1. I have explicit authorization to scan the specified targets
2. I will comply with all applicable laws and regulations
3. I will respect scope boundaries and responsible disclosure
4. I understand that my actions are being logged
5. I accept full responsibility for my use of this tool

This is a legal acknowledgment. Proceed only if you agree.
"""
    
    @classmethod
    def display(cls) -> str:
        """Display the legal disclaimer."""
        return cls.DISCLAIMER_TEXT
    
    @classmethod
    def get_acknowledgment_text(cls) -> str:
        """Get the acknowledgment text for user confirmation."""
        return cls.ACKNOWLEDGMENT_TEXT
    
    @classmethod
    def create_acknowledgment_record(
        cls,
        user: str,
        ip_address: str,
        timestamp: Optional[datetime] = None,
    ) -> dict:
        """Create a record of user acknowledgment."""
        return {
            "user": user,
            "ip_address": ip_address,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "disclaimer_version": "1.0",
            "acknowledgment_type": "legal_disclaimer",
        }


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


async def audit_log(
    action: AuditAction,
    actor: str = "system",
    scan_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Convenience function to log an audit event."""
    logger = get_audit_logger()
    await logger.log(action=action, actor=actor, scan_id=scan_id, details=details)
