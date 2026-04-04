"""Configuration management for HiveRecon."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AIConfig(BaseModel):
    """AI/LLM configuration."""
    provider: str = "groq"
    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.3
    max_tokens: int = 4096


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "data/hiverecon.db"
    echo: bool = False


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"])


class ToolsConfig(BaseModel):
    """Recon tool paths configuration."""
    subfinder: Optional[str] = None
    amass: Optional[str] = None
    nmap: Optional[str] = None
    katana: Optional[str] = None
    ffuf: Optional[str] = None
    nuclei: Optional[str] = None


class ScanConfig(BaseModel):
    """Scan execution configuration."""
    max_concurrent_agents: int = 5
    timeout_minutes: int = 120
    retries: int = 3


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "data/logs/hiverecon.log"
    audit_file: str = "data/audit/audit.log"


class LegalConfig(BaseModel):
    """Legal compliance configuration."""
    require_acknowledgment: bool = True
    disclaimer_on_startup: bool = True
    audit_all_actions: bool = True


class DashboardConfig(BaseModel):
    """Dashboard configuration."""
    enabled: bool = True
    theme: str = "dark"


class Config(BaseSettings):
    """Main configuration class."""
    
    ai: AIConfig = Field(default_factory=AIConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    scan: ScanConfig = Field(default_factory=ScanConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    legal: LegalConfig = Field(default_factory=LegalConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    
    # Environment overrides
    groq_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    database_url: Optional[str] = None
    api_host: Optional[str] = None
    api_port: Optional[int] = None
    secret_key: str = "change-this-to-a-random-secret-key-in-production"
    
    class Config:
        env_prefix = ""
        env_file = ".env"
    
    @classmethod
    def load(cls, config_path: str = "config/config.yaml") -> "Config":
        """Load configuration from YAML file with environment overrides."""
        config_file = Path(config_path)
        
        if config_file.exists():
            with open(config_file) as f:
                yaml_data = yaml.safe_load(f)
        else:
            yaml_data = {}
        
        config = cls(**yaml_data)

        if config.groq_api_key:
            # GROQ_API_KEY is used directly via env var
            pass
        if config.ai_model:
            config.ai.model = config.ai_model
        if config.api_host:
            config.api.host = config.api_host
        if config.api_port:
            config.api.port = config.api_port

        return config
    
    def get_database_url(self) -> str:
        """Get the database URL."""
        # Prioritize DATABASE_URL environment variable
        env_url = os.environ.get("DATABASE_URL")
        if env_url:
            return env_url
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.database.path}"


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config
