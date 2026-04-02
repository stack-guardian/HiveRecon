from langchain_core.prompts import PromptTemplate

# 1. Vulnerability Explanation Prompt
VULN_EXPLANATION_PROMPT = PromptTemplate(
    input_variables=["name", "severity", "url", "parameter", "evidence"],
    template="""
You are an expert bug bounty hunter and security researcher.
Analyze the following vulnerability finding and provide a high-quality explanation.

FINDING DETAILS:
- Name: {name}
- Severity: {severity}
- URL: {url}
- Parameter: {parameter}
- Evidence: {evidence}

Please generate:
1. **Plain-English Explanation**: What is this vulnerability in simple terms?
2. **Bug Bounty Context**: Why does this matter to a researcher and why would a company pay for it? (Impact)
3. **Likely Root Cause**: What developer mistake typically leads to this?
4. **Remediation**: 2-3 concise sentences on how to fix it permanently.
5. **CVSS Estimate**: A numerical CVSS v3.1 score (e.g., 7.5) with a brief 1-sentence justification.

Provide the response in a structured, professional format.
"""
)

# 2. Scope Validation Prompt
SCOPE_VALIDATION_PROMPT = PromptTemplate(
    input_variables=["target_domain", "subdomains"],
    template="""
You are HiveRecon's Legal Compliance AI. 
Analyze the discovered subdomains for the target: {target_domain}

Discovered Subdomains:
{subdomains}

Classify each subdomain into one of these categories:
- in-scope: Directly related to the target and should be scanned.
- out-of-scope: Third-party services (e.g., Zendesk, Shopify) that aren't part of the bounty program or sensitive infrastructure.
- ambiguous: Needs further manual review.

Format your response as a JSON list of objects:
[
  {{
    "subdomain": "sub.example.com",
    "status": "in-scope/out-of-scope/ambiguous",
    "reason": "One-line reasoning for this classification"
  }}
]
"""
)

# 3. Correlation Insight Prompt
CORRELATION_INSIGHT_PROMPT = PromptTemplate(
    input_variables=["findings"],
    template="""
You are a Lead Security Architect. Analyze these correlated findings and build an attack narrative.

FINDINGS:
{findings}

Generate a concise attack narrative:
- How could an attacker chain these findings together?
- What is the most likely end goal of such an attack?
- What is the overall risk to the organization?

Be technical, concise, and focused on the attack path.
"""
)

class PromptLibrary:
    """Library for accessing HiveRecon AI prompts."""
    
    _prompts = {
        "vuln_explanation": VULN_EXPLANATION_PROMPT,
        "scope_validation": SCOPE_VALIDATION_PROMPT,
        "correlation_insight": CORRELATION_INSIGHT_PROMPT,
    }

    @classmethod
    def get(cls, name: str) -> PromptTemplate:
        """Get a prompt template by name."""
        prompt = cls._prompts.get(name)
        if not prompt:
            raise ValueError(f"Prompt '{name}' not found in library.")
        return prompt
