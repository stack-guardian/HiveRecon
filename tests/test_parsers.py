"""Tests for recon tool parsers."""

import pytest
from hiverecon.core.parsers import (
    SubfinderParser,
    NmapParser,
    NucleiParser,
    ParsedResult,
)


class TestSubfinderParser:
    """Tests for Subfinder output parser."""
    
    def test_parse_plain_text(self):
        parser = SubfinderParser()
        output = """subdomain1.example.com
subdomain2.example.com
subdomain3.example.com"""
        
        results = parser.parse(output)
        
        assert len(results) == 3
        assert all(r.finding_type == "subdomain" for r in results)
        assert "subdomain1.example.com" in [r.value for r in results]
    
    def test_parse_json_output(self):
        parser = SubfinderParser()
        output = '{"host":"subdomain.example.com","ip":"1.2.3.4"}'
        
        results = parser.parse(output)
        
        assert len(results) == 1
        assert results[0].value == "subdomain.example.com"
        assert results[0].metadata.get("ip") == "1.2.3.4"
    
    def test_parse_empty_output(self):
        parser = SubfinderParser()
        output = ""
        
        results = parser.parse(output)
        
        assert len(results) == 0
    
    def test_parse_invalid_domains(self):
        parser = SubfinderParser()
        output = """valid.example.com
invalid_domain
also-valid.example.com"""
        
        results = parser.parse(output)
        
        # Should filter invalid domains
        assert len(results) >= 1


class TestNmapParser:
    """Tests for Nmap output parser."""
    
    def test_parse_open_ports(self):
        parser = NmapParser()
        output = """Nmap scan report for example.com
Host is up
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
443/tcp open https"""
        
        results = parser.parse(output)
        
        assert len(results) == 3
        assert any("22" in r.value for r in results)
        assert any("80" in r.value for r in results)
    
    def test_parse_high_risk_ports(self):
        parser = NmapParser()
        output = """Nmap scan report for example.com
PORT     STATE SERVICE
3306/tcp open  mysql"""
        
        results = parser.parse(output)
        
        assert len(results) == 1
        assert results[0].severity == "high"  # MySQL is high risk
    
    def test_parse_filtered_ports(self):
        parser = NmapParser()
        output = """Nmap scan report for example.com
PORT   STATE SERVICE
22/tcp open  ssh
23/tcp filtered telnet"""
        
        results = parser.parse(output)
        
        # Only open ports should be included
        assert len(results) == 1
        assert "22" in results[0].value


class TestNucleiParser:
    """Tests for Nuclei vulnerability scanner parser."""
    
    def test_parse_vulnerabilities(self):
        parser = NucleiParser()
        output = '{"info":{"name":"XSS Vulnerability","severity":"high","description":"Cross-site scripting found"},"host":"https://example.com","matched-at":"https://example.com/search"}'
        
        results = parser.parse(output)
        
        assert len(results) == 1
        assert results[0].finding_type == "vulnerability"
        assert results[0].severity == "high"
        assert "XSS" in results[0].title
    
    def test_parse_multiple_vulnerabilities(self):
        parser = NucleiParser()
        output = """{"info":{"name":"XSS","severity":"medium"},"host":"https://example.com"}
{"info":{"name":"SQL Injection","severity":"critical"},"host":"https://example.com"}"""
        
        results = parser.parse(output)
        
        assert len(results) == 2
        severities = [r.severity for r in results]
        assert "medium" in severities
        assert "critical" in severities
    
    def test_parse_empty_output(self):
        parser = NucleiParser()
        output = ""
        
        results = parser.parse(output)
        
        assert len(results) == 0
    
    def test_parse_severity_mapping(self):
        parser = NucleiParser()
        
        # Test all severity levels
        for severity in ["critical", "high", "medium", "low", "info"]:
            output = f'{{"info":{{"name":"Test","severity":"{severity}"}}, "host":"http://test.com"}}'
            results = parser.parse(output)
            
            assert len(results) == 1
            assert results[0].severity == severity


class TestParsedResult:
    """Tests for ParsedResult dataclass."""
    
    def test_create_result(self):
        result = ParsedResult(
            finding_type="subdomain",
            value="test.example.com",
            severity="info",
        )
        
        assert result.finding_type == "subdomain"
        assert result.value == "test.example.com"
        assert result.severity == "info"
    
    def test_to_dict(self):
        result = ParsedResult(
            finding_type="open_port",
            value="example.com:80",
        )
        
        result_dict = result.to_dict()
        
        assert "finding_type" in result_dict
        assert "value" in result_dict
        assert "timestamp" in result_dict
    
    def test_default_values(self):
        result = ParsedResult(
            finding_type="test",
            value="test_value",
        )
        
        assert result.severity == "info"
        assert result.metadata == {}
        assert result.title == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
