"""Core module for HiveRecon."""

from hiverecon.core.hive_mind import HiveMindCoordinator
from hiverecon.core.parsers import (
    BaseParser,
    ParsedResult,
    get_parser,
    parse_output,
    SubfinderParser,
    AmassParser,
    NmapParser,
    KatanaParser,
    FfufParser,
    NucleiParser,
)
from hiverecon.core.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    ResourceManager,
    AgentScheduler,
    ScanQuota,
    get_scheduler,
    get_quota,
)
from hiverecon.core.correlation import (
    FindingsCorrelator,
    FalsePositiveDetector,
    ConfidenceScore,
    get_correlator,
    correlate_findings,
)
from hiverecon.core.audit import (
    AuditLogger,
    AuditAction,
    LegalDisclaimer,
    get_audit_logger,
    audit_log,
)

__all__ = [
    "HiveMindCoordinator",
    "BaseParser",
    "ParsedResult",
    "get_parser",
    "parse_output",
    "SubfinderParser",
    "AmassParser",
    "NmapParser",
    "KatanaParser",
    "FfufParser",
    "NucleiParser",
    "RateLimiter",
    "RateLimitConfig",
    "ResourceManager",
    "AgentScheduler",
    "ScanQuota",
    "get_scheduler",
    "get_quota",
    "FindingsCorrelator",
    "FalsePositiveDetector",
    "ConfidenceScore",
    "get_correlator",
    "correlate_findings",
    "AuditLogger",
    "AuditAction",
    "LegalDisclaimer",
    "get_audit_logger",
    "audit_log",
]
