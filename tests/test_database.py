"""Tests for database operations."""

import pytest
import asyncio
from pathlib import Path

from hiverecon.database import (
    init_db,
    Scan,
    Target,
    Finding,
    FindingSeverity,
    AgentType,
    ScanStatus,
)
from hiverecon.config import get_config


@pytest.fixture
async def db_session():
    """Create test database session."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Use in-memory SQLite for tests
    database_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Scan.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_scan(db_session):
    """Test creating a scan."""
    scan = Scan(
        id="test123",
        target_domain="example.com",
        platform="hackerone",
        status=ScanStatus.PENDING,
    )
    
    db_session.add(scan)
    await db_session.commit()
    
    # Verify
    result = await db_session.get(Scan, "test123")
    assert result is not None
    assert result.target_domain == "example.com"
    assert result.status == ScanStatus.PENDING


@pytest.mark.asyncio
async def test_create_target(db_session):
    """Test creating a target."""
    scan = Scan(
        id="test123",
        target_domain="example.com",
        status=ScanStatus.PENDING,
    )
    db_session.add(scan)
    await db_session.commit()
    
    target = Target(
        scan_id="test123",
        target_type="domain",
        target_value="example.com",
        in_scope=True,
        validated=True,
    )
    db_session.add(target)
    await db_session.commit()
    
    result = await db_session.get(Target, target.id)
    assert result is not None
    assert result.target_value == "example.com"
    assert result.in_scope == True


@pytest.mark.asyncio
async def test_create_finding(db_session):
    """Test creating a finding."""
    scan = Scan(
        id="test123",
        target_domain="example.com",
        status=ScanStatus.PENDING,
    )
    db_session.add(scan)
    
    target = Target(
        scan_id="test123",
        target_type="domain",
        target_value="example.com",
        in_scope=True,
    )
    db_session.add(target)
    await db_session.commit()
    
    finding = Finding(
        scan_id="test123",
        target_id=target.id,
        agent_type=AgentType.SUBDOMAIN,
        finding_type="subdomain",
        severity=FindingSeverity.INFO,
        title="Subdomain found",
        location="test.example.com",
    )
    db_session.add(finding)
    await db_session.commit()
    
    result = await db_session.get(Finding, finding.id)
    assert result is not None
    assert result.severity == FindingSeverity.INFO
    assert result.location == "test.example.com"


@pytest.mark.asyncio
async def test_scan_relationships(db_session):
    """Test scan relationships with targets and findings."""
    scan = Scan(
        id="test123",
        target_domain="example.com",
        status=ScanStatus.PENDING,
    )
    db_session.add(scan)
    await db_session.commit()
    
    # Add targets
    for i in range(3):
        target = Target(
            scan_id="test123",
            target_type="domain",
            target_value=f"sub{i}.example.com",
            in_scope=True,
        )
        db_session.add(target)
    
    await db_session.commit()
    
    # Verify relationship - use explicit query instead of refresh
    from sqlalchemy import select
    result = await db_session.execute(
        select(Scan).where(Scan.id == "test123")
    )
    scan_result = result.scalar()
    await db_session.refresh(scan_result)
    
    assert len(scan_result.targets) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
