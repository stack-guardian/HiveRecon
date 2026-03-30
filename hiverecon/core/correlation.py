"""
False positive detection and findings correlation.

Uses heuristics and AI to reduce noise and prioritize real vulnerabilities.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from hiverecon.database import Finding, FindingSeverity


@dataclass
class ConfidenceScore:
    """Confidence scoring for findings."""
    
    base_score: float = 0.5  # 0-1 scale
    factors: dict[str, float] = field(default_factory=dict)
    
    def calculate(self) -> float:
        """Calculate final confidence score."""
        score = self.base_score
        for factor, weight in self.factors.items():
            score += weight
        return max(0.0, min(1.0, score))
    
    def add_factor(self, name: str, weight: float) -> None:
        """Add a confidence factor."""
        self.factors[name] = weight


class FalsePositiveDetector:
    """
    Detects likely false positives using heuristics and patterns.
    
    Common false positive sources:
    - CDN/error pages matching keywords
    - Default framework pages
    - Rate-limited/blocked requests
    - Captcha pages
    """
    
    # Keywords that often indicate false positives
    FP_KEYWORDS = {
        "cloudflare": 0.8,
        "access denied": 0.7,
        "captcha": 0.6,
        "rate limit": 0.7,
        "blocked": 0.6,
        "forbidden": 0.5,
        "error page": 0.4,
        "default page": 0.5,
        "coming soon": 0.6,
        "under construction": 0.6,
        "nginx default": 0.7,
        "apache default": 0.7,
        "404 not found": 0.3,  # Could be real
        "page not found": 0.3,
    }
    
    # Patterns that indicate false positives
    FP_PATTERNS = {
        r"content-length:\s*0": 0.8,
        r"server:\s*cloudflare": 0.6,
        r"x-frame-options:\s*DENY": 0.3,  # Just security header
        r"strict-transport-security": 0.2,  # Just security header
    }
    
    # Status codes that need verification
    SUSPICIOUS_STATUS_CODES = {
        200: 0.0,   # Could be real or FP
        301: 0.1,   # Redirect - usually OK
        302: 0.2,   # Temp redirect - verify
        401: 0.3,   # Auth required - could be real
        403: 0.4,   # Forbidden - interesting
        404: 0.6,   # Not found - likely FP for endpoints
        500: 0.5,   # Server error - could be real bug
    }
    
    def is_likely_false_positive(
        self,
        finding: Finding,
        additional_context: Optional[dict] = None,
    ) -> tuple[bool, float, str]:
        """
        Check if a finding is likely a false positive.
        
        Returns: (is_fp, confidence, reason)
        """
        reasons = []
        confidence = 0.0
        
        # Get evidence/content for analysis
        evidence = finding.evidence or {}
        raw_output = str(evidence.get("raw", finding.description or ""))
        raw_lower = raw_output.lower()
        
        # Check for FP keywords
        for keyword, weight in self.FP_KEYWORDS.items():
            if keyword in raw_lower:
                reasons.append(f"Contains FP keyword: '{keyword}'")
                confidence = max(confidence, weight)
        
        # Check response characteristics
        status_code = evidence.get("status", evidence.get("status_code", 0))
        if status_code in self.SUSPICIOUS_STATUS_CODES:
            fp_weight = self.SUSPICIOUS_STATUS_CODES[status_code]
            if fp_weight > 0.5:
                reasons.append(f"Status code {status_code} suggests FP")
                confidence = max(confidence, fp_weight)
        
        # Check content length (very short/long often indicates FP)
        content_length = evidence.get("length", evidence.get("content_length", 0))
        if content_length and (content_length < 100 or content_length > 100000):
            reasons.append(f"Suspicious content length: {content_length}")
            confidence = max(confidence, 0.4)
        
        # Type-specific checks
        if finding.finding_type == "endpoint":
            confidence = max(confidence, self._check_endpoint_fp(finding, evidence))
        elif finding.finding_type == "vulnerability":
            confidence = max(confidence, self._check_vulnerability_fp(finding, evidence))
        elif finding.finding_type == "subdomain":
            confidence = max(confidence, self._check_subdomain_fp(finding, evidence))
        
        is_fp = confidence > 0.6
        reason = "; ".join(reasons) if reasons else "No FP indicators found"
        
        return is_fp, confidence, reason
    
    def _check_endpoint_fp(self, finding: Finding, evidence: dict) -> float:
        """Check if endpoint finding is likely FP."""
        confidence = 0.0
        
        # Common false positive endpoints
        fp_endpoints = [
            "/robots.txt",
            "/sitemap.xml",
            "/favicon.ico",
            "/.well-known/",
            "/css/",
            "/js/",
            "/images/",
        ]
        
        location = finding.location or ""
        for fp_endpoint in fp_endpoints:
            if fp_endpoint in location.lower():
                confidence = max(confidence, 0.7)
                break
        
        return confidence
    
    def _check_vulnerability_fp(self, finding: Finding, evidence: dict) -> float:
        """Check if vulnerability finding is likely FP."""
        confidence = 0.0
        
        # Check if it's an informational finding mislabeled as vulnerability
        template_id = evidence.get("template_id", evidence.get("template-id", ""))
        if "info" in template_id.lower() or "detect" in template_id.lower():
            confidence = max(confidence, 0.5)
        
        # Check for generic matches
        matcher_name = evidence.get("matcher_name", evidence.get("matcher-name", ""))
        if "generic" in matcher_name.lower():
            confidence = max(confidence, 0.4)
        
        return confidence
    
    def _check_subdomain_fp(self, finding: Finding, evidence: dict) -> float:
        """Check if subdomain finding is likely FP."""
        confidence = 0.0

        # Wildcard DNS patterns that create false positives
        value = finding.location or ""

        # Check for CDN/provider subdomains that are often wildcards
        cdn_patterns = [
            ".cloudfront.net",
            ".herokuapp.com",
            ".github.io",
            ".gitlab.io",
            ".shopify.com",
        ]

        for pattern in cdn_patterns:
            if value.endswith(pattern):
                confidence = max(confidence, 0.3)  # Not necessarily FP, just note it
                break
        
        return confidence


class FindingsCorrelator:
    """
    Correlates findings across different agents/tools.
    
    Features:
    - Groups related findings
    - Identifies attack chains
    - Prioritizes based on combined evidence
    - Deduplicates similar findings
    """
    
    def __init__(self):
        self.fp_detector = FalsePositiveDetector()
    
    def correlate(self, findings: list[Finding]) -> list[Finding]:
        """
        Correlate and prioritize findings.
        
        Returns findings with updated metadata including:
        - correlation_group: ID of related findings
        - priority_score: Combined priority score
        - is_false_positive: FP detection result
        """
        # Step 1: Deduplicate
        unique_findings = self._deduplicate(findings)
        
        # Step 2: Group related findings
        groups = self._group_by_target(unique_findings)
        
        # Step 3: Correlate within groups
        correlated = []
        for group_id, group_findings in groups.items():
            correlated_group = self._correlate_group(group_findings, group_id)
            correlated.extend(correlated_group)
        
        # Step 4: Apply FP detection and sort by priority
        for finding in correlated:
            is_fp, fp_confidence, fp_reason = self.fp_detector.is_likely_false_positive(
                finding
            )
            finding.ai_analysis = finding.ai_analysis or {}
            finding.ai_analysis.update({
                "is_false_positive": is_fp,
                "fp_confidence": fp_confidence,
                "fp_reason": fp_reason,
                "priority_score": self._calculate_priority(finding),
            })
        
        # Sort by priority (highest first), exclude likely FPs
        correlated.sort(
            key=lambda f: (
                f.ai_analysis.get("priority_score", 0) if not f.ai_analysis.get("is_false_positive", False) else -1,
                self._severity_order(f.severity),
            ),
            reverse=True
        )
        
        return correlated
    
    def _deduplicate(self, findings: list[Finding]) -> list[Finding]:
        """Remove duplicate findings."""
        seen = set()
        unique = []
        
        for finding in findings:
            # Create a hashable key from finding attributes
            key = (
                finding.finding_type,
                finding.location or finding.value,
                finding.title,
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        
        return unique
    
    def _group_by_target(self, findings: list[Finding]) -> dict[str, list[Finding]]:
        """Group findings by target host/domain."""
        groups = defaultdict(list)
        
        for finding in findings:
            # Extract host from location/value
            location = finding.location or finding.value or ""
            host = self._extract_host(location)
            groups[host].append(finding)
        
        return dict(groups)
    
    def _correlate_group(
        self,
        findings: list[Finding],
        group_id: str,
    ) -> list[Finding]:
        """Correlate findings within a group."""
        if len(findings) <= 1:
            for finding in findings:
                self._add_finding_context(finding, findings)
            return findings
        
        # Findings in a group with multiple discoveries are more significant
        for finding in findings:
            finding.ai_analysis = finding.ai_analysis or {}
            finding.ai_analysis["correlation_group"] = group_id
            finding.ai_analysis["related_findings_count"] = len(findings) - 1
            
            # Boost priority for findings with related discoveries
            if len(findings) >= 3:
                finding.ai_analysis["multi_finding_boost"] = 0.2
            elif len(findings) >= 2:
                finding.ai_analysis["multi_finding_boost"] = 0.1
            
            self._add_finding_context(finding, findings)
        
        return findings
    
    def _add_finding_context(self, finding: Finding, all_findings: list[Finding]) -> None:
        """Add contextual information to a finding."""
        # Find related vulnerabilities that could chain
        if finding.finding_type == "vulnerability":
            related = []
            for other in all_findings:
                if other.id != finding.id:
                    if other.finding_type == "open_port":
                        related.append(f"Open port may expose vulnerable service: {other.location}")
                    elif other.finding_type == "endpoint":
                        related.append(f"Related endpoint: {other.location}")
            
            if related:
                finding.ai_analysis = finding.ai_analysis or {}
                finding.ai_analysis["related_context"] = related
    
    def _calculate_priority(self, finding: Finding) -> float:
        """Calculate priority score for a finding."""
        base_scores = {
            FindingSeverity.CRITICAL: 1.0,
            FindingSeverity.HIGH: 0.8,
            FindingSeverity.MEDIUM: 0.6,
            FindingSeverity.LOW: 0.4,
            FindingSeverity.INFO: 0.2,
        }
        
        score = base_scores.get(finding.severity, 0.2)
        
        # Apply boosts from AI analysis
        analysis = finding.ai_analysis or {}
        
        # Multi-finding boost
        score += analysis.get("multi_finding_boost", 0)
        
        # Related findings boost
        if analysis.get("related_findings_count", 0) >= 3:
            score += 0.15
        elif analysis.get("related_findings_count", 0) >= 1:
            score += 0.05
        
        # Vulnerability type boost
        if finding.finding_type == "vulnerability":
            title_lower = (finding.title or "").lower()
            high_impact_keywords = ["rce", "sql injection", "ssrf", "auth bypass", "idors"]
            for keyword in high_impact_keywords:
                if keyword in title_lower:
                    score += 0.2
                    break
        
        return min(1.0, score)
    
    def _extract_host(self, url: str) -> str:
        """Extract host from URL or host:port string."""
        if not url:
            return "unknown"
        
        # Remove protocol
        url = url.replace("https://", "").replace("http://", "")
        
        # Extract host (before first / or :)
        host = url.split("/")[0].split(":")[0]
        
        return host or "unknown"
    
    def _severity_order(self, severity: FindingSeverity) -> int:
        """Get numeric order for severity."""
        order = {
            FindingSeverity.CRITICAL: 5,
            FindingSeverity.HIGH: 4,
            FindingSeverity.MEDIUM: 3,
            FindingSeverity.LOW: 2,
            FindingSeverity.INFO: 1,
        }
        return order.get(severity, 0)


# Global correlator instance
_correlator: Optional[FindingsCorrelator] = None


def get_correlator() -> FindingsCorrelator:
    """Get the global findings correlator."""
    global _correlator
    if _correlator is None:
        _correlator = FindingsCorrelator()
    return _correlator


def correlate_findings(findings: list[Finding]) -> list[Finding]:
    """Convenience function to correlate findings."""
    return get_correlator().correlate(findings)
