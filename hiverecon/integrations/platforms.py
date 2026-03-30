"""Bug Bounty Platform Integrations."""

from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx


class BasePlatform(ABC):
    """Base class for bug bounty platform integrations."""
    
    name: str
    base_url: str
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=30.0,
        )
    
    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers
    
    @abstractmethod
    async def get_program_scope(self, program_id: str) -> dict[str, Any]:
        """Fetch program scope (in-scope and out-of-scope targets)."""
        pass
    
    @abstractmethod
    async def validate_target(self, target: str, program_id: str) -> bool:
        """Validate if a target is in scope for a program."""
        pass
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class HackerOnePlatform(BasePlatform):
    """HackerOne platform integration."""
    
    name = "hackerone"
    base_url = "https://api.hackerone.com/v1"
    
    async def get_program_scope(self, program_id: str) -> dict[str, Any]:
        """Fetch HackerOne program scope."""
        if not self.api_token:
            return {"in_scope": [], "out_of_scope": []}
        
        try:
            response = await self.client.get(f"/programs/{program_id}")
            response.raise_for_status()
            data = response.json()
            
            program = data.get("data", {})
            attributes = program.get("attributes", {})
            
            in_scope = []
            out_of_scope = []
            
            # Parse asset scopes
            for asset in attributes.get("structured_scope", {}).get("domains", []):
                target = {
                    "type": "domain",
                    "value": asset.get("domain_name", ""),
                    "instruction": asset.get("instruction", ""),
                }
                if asset.get("eligible_for_submission", True):
                    in_scope.append(target)
                else:
                    out_of_scope.append(target)
            
            return {"in_scope": in_scope, "out_of_scope": out_of_scope}
            
        except httpx.HTTPError as e:
            return {"error": str(e), "in_scope": [], "out_of_scope": []}
    
    async def validate_target(self, target: str, program_id: str) -> bool:
        """Validate target against HackerOne program scope."""
        scope = await self.get_program_scope(program_id)
        
        for in_scope_target in scope.get("in_scope", []):
            if self._target_matches(target, in_scope_target.get("value", "")):
                return True
        
        return False
    
    def _target_matches(self, target: str, scope_pattern: str) -> bool:
        """Check if target matches scope pattern (supports wildcards)."""
        if scope_pattern.startswith("*."):
            # Wildcard: *.example.com matches sub.example.com
            base = scope_pattern[2:]
            return target.endswith(base) or target == base
        return target == scope_pattern or target.endswith(f".{scope_pattern}")


class BugcrowdPlatform(BasePlatform):
    """Bugcrowd platform integration."""
    
    name = "bugcrowd"
    base_url = "https://api.bugcrowd.com"
    
    async def get_program_scope(self, program_id: str) -> dict[str, Any]:
        """Fetch Bugcrowd program scope."""
        if not self.api_token:
            return {"in_scope": [], "out_of_scope": []}
        
        try:
            response = await self.client.get(f"/programs/{program_id}/targets")
            response.raise_for_status()
            data = response.json()
            
            in_scope = []
            out_of_scope = []
            
            for target in data.get("targets", []):
                target_data = {
                    "type": target.get("target_type", "domain"),
                    "value": target.get("target_value", ""),
                    "instruction": target.get("instruction", ""),
                }
                if target.get("in_scope", True):
                    in_scope.append(target_data)
                else:
                    out_of_scope.append(target_data)
            
            return {"in_scope": in_scope, "out_of_scope": out_of_scope}
            
        except httpx.HTTPError as e:
            return {"error": str(e), "in_scope": [], "out_of_scope": []}
    
    async def validate_target(self, target: str, program_id: str) -> bool:
        """Validate target against Bugcrowd program scope."""
        scope = await self.get_program_scope(program_id)
        
        for in_scope_target in scope.get("in_scope", []):
            if target == in_scope_target.get("value", ""):
                return True
            # Check wildcard
            if in_scope_target.get("value", "").startswith("*."):
                base = in_scope_target["value"][2:]
                if target.endswith(base) or target == base:
                    return True
        
        return False


class IntigritiPlatform(BasePlatform):
    """Intigriti platform integration."""
    
    name = "intigriti"
    base_url = "https://api.intigriti.com"
    
    async def get_program_scope(self, program_id: str) -> dict[str, Any]:
        """Fetch Intigriti program scope."""
        if not self.api_token:
            return {"in_scope": [], "out_of_scope": []}
        
        try:
            response = await self.client.get(f"/programs/{program_id}/scope")
            response.raise_for_status()
            data = response.json()
            
            in_scope = []
            out_of_scope = []
            
            for item in data.get("scope", []):
                target_data = {
                    "type": item.get("type", "domain"),
                    "value": item.get("value", ""),
                    "instruction": item.get("instruction", ""),
                }
                if item.get("in_scope", True):
                    in_scope.append(target_data)
                else:
                    out_of_scope.append(target_data)
            
            return {"in_scope": in_scope, "out_of_scope": out_of_scope}
            
        except httpx.HTTPError as e:
            return {"error": str(e), "in_scope": [], "out_of_scope": []}
    
    async def validate_target(self, target: str, program_id: str) -> bool:
        """Validate target against Intigriti program scope."""
        scope = await self.get_program_scope(program_id)
        
        for in_scope_target in scope.get("in_scope", []):
            value = in_scope_target.get("value", "")
            if value.startswith("*."):
                base = value[2:]
                if target.endswith(base) or target == base:
                    return True
            elif target == value or target.endswith(f".{value}"):
                return True
        
        return False


# Platform registry
PLATFORM_REGISTRY = {
    "hackerone": HackerOnePlatform,
    "bugcrowd": BugcrowdPlatform,
    "intigriti": IntigritiPlatform,
}


def get_platform(platform_name: str, api_token: Optional[str] = None) -> BasePlatform:
    """Factory function to create platform instances."""
    platform_class = PLATFORM_REGISTRY.get(platform_name.lower())
    if not platform_class:
        raise ValueError(f"Unknown platform: {platform_name}")
    return platform_class(api_token)
