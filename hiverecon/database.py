"""Database models for HiveRecon."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class ScanStatus(str, Enum):
    """Scan execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FindingSeverity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AgentType(str, Enum):
    """Recon agent types."""
    SUBDOMAIN = "subdomain"
    PORT_SCAN = "port_scan"
    ENDPOINT = "endpoint"
    VULNERABILITY = "vulnerability"
    MCP = "mcp"


class Scan(Base):
    """Represents a reconnaissance scan."""
    
    __tablename__ = "scans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_domain = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=True)  # hackerone, bugcrowd, intigriti
    scope_config = Column(JSON, nullable=True)
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    targets = relationship("Target", back_populates="scan", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    agents = relationship("AgentRun", back_populates="scan", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="scan", cascade="all, delete-orphan")


class Target(Base):
    """Represents a target within a scan scope."""
    
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    target_type = Column(String, nullable=False)  # domain, wildcard, cidr, url
    target_value = Column(String, nullable=False)
    in_scope = Column(Boolean, default=True)
    validated = Column(Boolean, default=False)
    validation_notes = Column(Text, nullable=True)
    
    # Relationships
    scan = relationship("Scan", back_populates="targets")
    findings = relationship("Finding", back_populates="target", cascade="all, delete-orphan")


class Finding(Base):
    """Represents a discovered finding/vulnerability."""
    
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    finding_type = Column(String, nullable=False)  # subdomain, open_port, endpoint, vulnerability
    severity = Column(SQLEnum(FindingSeverity), default=FindingSeverity.INFO)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    evidence = Column(JSON, nullable=True)  # Raw output from tools
    location = Column(String, nullable=True)  # URL, host:port, etc.
    is_false_positive = Column(Boolean, default=False)
    ai_analysis = Column(JSON, nullable=True)  # AI-generated analysis and recommendations
    educational_content = Column(Text, nullable=True)  # Beginner-friendly explanation
    reproduction_steps = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scan = relationship("Scan", back_populates="findings")
    target = relationship("Target", back_populates="findings")


class AgentRun(Base):
    """Represents a single agent execution within a scan."""
    
    __tablename__ = "agent_runs"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING)
    command = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    findings_count = Column(Integer, default=0)
    
    # Relationships
    scan = relationship("Scan", back_populates="agents")


class AuditLog(Base):
    """Audit log for compliance and accountability."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=True)
    action = Column(String, nullable=False)
    actor = Column(String, default="system")  # user or system
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=True)
    
    # Relationships
    scan = relationship("Scan", back_populates="audit_logs")


class User(Base):
    """User accounts for dashboard access."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


async def init_db(database_url: str) -> None:
    """Initialize the database."""
    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def get_session(database_url: str) -> AsyncSession:
    """Get a database session."""
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
