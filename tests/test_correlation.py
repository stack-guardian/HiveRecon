"""Tests for HiveRecon core modules."""

import pytest
from hiverecon.core.correlation import (
    FalsePositiveDetector,
    FindingsCorrelator,
    correlate_findings,
)
from hiverecon.database import Finding, FindingSeverity, AgentType


class TestFalsePositiveDetector:
    """Tests for false positive detection."""
    
    def test_detect_cloudflare_fp(self):
        detector = FalsePositiveDetector()
        finding = Finding(
            finding_type="endpoint",
            value="https://example.com",
            description="Cloudflare access denied page",
            evidence={"raw": "Cloudflare protection enabled"},
        )
        
        is_fp, confidence, reason = detector.is_likely_false_positive(finding)
        
        assert is_fp == True
        assert confidence > 0.5
    
    def test_not_false_positive(self):
        detector = FalsePositiveDetector()
        finding = Finding(
            finding_type="vulnerability",
            value="https://example.com/api",
            severity=FindingSeverity.HIGH,
            title="SQL Injection",
            description="SQL injection in login form",
        )
        
        is_fp, confidence, reason = detector.is_likely_false_positive(finding)
        
        assert is_fp == False
    
    def test_endpoint_fp_detection(self):
        detector = FalsePositiveDetector()
        finding = Finding(
            finding_type="endpoint",
            value="https://example.com/robots.txt",
            description="Common file",
        )
        
        is_fp, confidence, reason = detector.is_likely_false_positive(finding)
        
        # robots.txt is often a false positive in recon
        assert confidence > 0.3


class TestFindingsCorrelator:
    """Tests for findings correlation."""
    
    def test_deduplicate_findings(self):
        correlator = FindingsCorrelator()
        findings = [
            Finding(
                finding_type="subdomain",
                value="www.example.com",
                title="Subdomain: www.example.com",
            ),
            Finding(
                finding_type="subdomain",
                value="www.example.com",
                title="Subdomain: www.example.com",
            ),
        ]
        
        unique = correlator._deduplicate(findings)
        
        assert len(unique) == 1
    
    def test_group_by_target(self):
        correlator = FindingsCorrelator()
        findings = [
            Finding(
                finding_type="subdomain",
                value="api.example.com",
                location="https://api.example.com",
            ),
            Finding(
                finding_type="open_port",
                value="api.example.com:443",
                location="https://api.example.com:443",
            ),
            Finding(
                finding_type="subdomain",
                value="www.example.com",
                location="https://www.example.com",
            ),
        ]
        
        groups = correlator._group_by_target(findings)
        
        # Should group api.example.com findings together
        assert len(groups) == 2
        assert len(groups.get("api.example.com", [])) == 2
    
    def test_priority_calculation(self):
        correlator = FindingsCorrelator()
        
        critical_finding = Finding(
            finding_type="vulnerability",
            severity=FindingSeverity.CRITICAL,
            title="RCE Vulnerability",
        )
        
        info_finding = Finding(
            finding_type="subdomain",
            severity=FindingSeverity.INFO,
            title="Subdomain discovered",
        )
        
        critical_score = correlator._calculate_priority(critical_finding)
        info_score = correlator._calculate_priority(info_finding)
        
        assert critical_score > info_score
    
    def test_correlate_findings(self):
        correlator = FindingsCorrelator()
        findings = [
            Finding(
                finding_type="vulnerability",
                severity=FindingSeverity.HIGH,
                title="XSS Vulnerability",
                location="https://example.com/search",
            ),
            Finding(
                finding_type="open_port",
                severity=FindingSeverity.LOW,
                title="Port 80 open",
                location="http://example.com:80",
            ),
        ]
        
        correlated = correlator.correlate(findings)
        
        assert len(correlated) == 2
        # High severity should be first
        assert correlated[0].severity == FindingSeverity.HIGH


class TestConvenienceFunctions:
    """Tests for module convenience functions."""
    
    def test_correlate_findings_function(self):
        findings = [
            Finding(
                finding_type="subdomain",
                value="test.example.com",
            ),
        ]
        
        correlated = correlate_findings(findings)
        
        assert len(correlated) == 1
        assert correlated[0].ai_analysis is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
