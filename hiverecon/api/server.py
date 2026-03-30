"""
FastAPI backend for HiveRecon dashboard.

Provides REST API for scan management, findings, and reports.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from hiverecon import __version__
from hiverecon.config import get_config
from hiverecon.database import Scan, ScanStatus, init_db, Finding, FindingSeverity
from hiverecon.core import (
    HiveMindCoordinator,
    get_audit_logger,
    AuditAction,
    audit_log,
)


# Initialize FastAPI app
app = FastAPI(
    title="HiveRecon API",
    description="AI-Powered Reconnaissance Framework API",
    version=__version__,
)

# CORS middleware
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Pydantic Models ==============

class ScanCreateRequest(BaseModel):
    """Request model for creating a scan."""
    target: str = Field(..., description="Target domain")
    platform: Optional[str] = Field(None, description="Bug bounty platform")
    program_id: Optional[str] = Field(None, description="Program ID")
    scope_config: Optional[dict] = Field(None, description="Scope configuration")


class ScanResponse(BaseModel):
    """Response model for scan."""
    scan_id: str
    target: str
    platform: Optional[str]
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class FindingResponse(BaseModel):
    """Response model for finding."""
    id: int
    finding_type: str
    severity: str
    title: str
    description: Optional[str]
    location: Optional[str]
    ai_analysis: Optional[dict]
    educational_content: Optional[str]
    created_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    ollama_connected: bool


# ============== Helper Functions ==============

async def get_db_session():
    """Get database session."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    config = get_config()
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session


async def run_scan_background(scan_id: str, target: str, platform: Optional[str], scope_config: dict):
    """Run scan in background."""
    audit_logger = get_audit_logger()
    
    try:
        await audit_log(
            action=AuditAction.SCAN_STARTED,
            actor="api",
            scan_id=scan_id,
            details={"target": target, "platform": platform},
        )
        
        # Initialize coordinator and run scan
        # Note: Full implementation would use the HiveMindCoordinator
        # This is a simplified version
        
        # Simulate scan progress
        await asyncio.sleep(5)
        
        await audit_log(
            action=AuditAction.SCAN_COMPLETED,
            actor="system",
            scan_id=scan_id,
        )
        
    except Exception as e:
        await audit_logger.log(
            action=AuditAction.SCAN_FAILED,
            actor="system",
            scan_id=scan_id,
            details={"error": str(e)},
        )


# ============== API Endpoints ==============

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": "HiveRecon API",
        "version": __version__,
        "description": "AI-Powered Reconnaissance Framework",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    # Check Ollama connection
    ollama_connected = False
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{config.ai.base_url}/api/tags", timeout=2)
            ollama_connected = response.status_code == 200
    except Exception:
        pass
    
    return {
        "status": "healthy",
        "version": __version__,
        "ollama_connected": ollama_connected,
    }


@app.post("/scans", response_model=ScanResponse, tags=["Scans"])
async def create_scan(request: ScanCreateRequest, background_tasks: BackgroundTasks):
    """Create a new reconnaissance scan."""
    scan_id = str(uuid.uuid4())[:8]
    
    # Create scan record
    config = get_config()
    await init_db(config.get_database_url())
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        scan = Scan(
            id=scan_id,
            target_domain=request.target,
            platform=request.platform,
            scope_config=request.scope_config,
            status=ScanStatus.PENDING,
        )
        session.add(scan)
        await session.commit()
    
    # Start scan in background
    background_tasks.add_task(
        run_scan_background,
        scan_id,
        request.target,
        request.platform,
        request.scope_config or {},
    )
    
    return ScanResponse(
        scan_id=scan_id,
        target=request.target,
        platform=request.platform,
        status=ScanStatus.PENDING.value,
        created_at=datetime.utcnow(),
        started_at=None,
        completed_at=None,
    )


@app.get("/scans", tags=["Scans"])
async def list_scans(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
):
    """List all scans with optional filtering."""
    config = get_config()
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        
        query = select(Scan)
        if status:
            query = query.where(Scan.status == status)
        query = query.order_by(Scan.created_at.desc()).limit(limit).offset(offset)
        
        result = await session.execute(query)
        scans = result.scalars().all()
        
        return {
            "scans": [
                {
                    "scan_id": scan.id,
                    "target": scan.target_domain,
                    "platform": scan.platform,
                    "status": scan.status.value,
                    "created_at": scan.created_at,
                }
                for scan in scans
            ],
            "total": len(scans),
        }


@app.get("/scans/{scan_id}", tags=["Scans"])
async def get_scan(scan_id: str):
    """Get details of a specific scan."""
    config = get_config()
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        scan = await session.get(Scan, scan_id)
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        return {
            "scan_id": scan.id,
            "target": scan.target_domain,
            "platform": scan.platform,
            "status": scan.status.value,
            "created_at": scan.created_at,
            "started_at": scan.started_at,
            "completed_at": scan.completed_at,
            "scope_config": scan.scope_config,
        }


@app.get("/scans/{scan_id}/findings", tags=["Findings"])
async def get_scan_findings(
    scan_id: str,
    severity: Optional[str] = None,
    finding_type: Optional[str] = None,
):
    """Get findings for a specific scan."""
    config = get_config()
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        
        query = select(Finding).where(Finding.scan_id == scan_id)
        
        if severity:
            query = query.where(Finding.severity == severity)
        if finding_type:
            query = query.where(Finding.finding_type == finding_type)
        
        result = await session.execute(query)
        findings = result.scalars().all()
        
        return {
            "findings": [
                {
                    "id": f.id,
                    "finding_type": f.finding_type,
                    "severity": f.severity.value,
                    "title": f.title,
                    "description": f.description,
                    "location": f.location,
                    "ai_analysis": f.ai_analysis,
                }
                for f in findings
            ],
            "total": len(findings),
        }


@app.delete("/scans/{scan_id}", tags=["Scans"])
async def cancel_scan(scan_id: str):
    """Cancel a running scan."""
    config = get_config()
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        scan = await session.get(Scan, scan_id)
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if scan.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
            raise HTTPException(status_code=400, detail="Scan cannot be cancelled")
        
        scan.status = ScanStatus.CANCELLED
        await session.commit()
        
        await audit_log(
            action=AuditAction.SCAN_CANCELLED,
            actor="api",
            scan_id=scan_id,
        )
        
        return {"message": "Scan cancelled", "scan_id": scan_id}


@app.get("/findings", tags=["Findings"])
async def list_findings(
    limit: int = Query(50, ge=1, le=500),
    severity: Optional[str] = None,
    include_fp: bool = Query(False, description="Include false positives"),
):
    """List findings across all scans."""
    config = get_config()
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        
        query = select(Finding).order_by(Finding.created_at.desc()).limit(limit)
        
        if severity:
            query = query.where(Finding.severity == severity)
        
        result = await session.execute(query)
        findings = result.scalars().all()
        
        # Filter false positives if requested
        if not include_fp:
            findings = [
                f for f in findings
                if not (f.ai_analysis or {}).get("is_false_positive", False)
            ]
        
        return {
            "findings": [
                {
                    "id": f.id,
                    "scan_id": f.scan_id,
                    "finding_type": f.finding_type,
                    "severity": f.severity.value,
                    "title": f.title,
                    "location": f.location,
                    "ai_analysis": f.ai_analysis,
                }
                for f in findings
            ],
            "total": len(findings),
        }


@app.get("/stats", tags=["Statistics"])
async def get_statistics():
    """Get overall statistics."""
    config = get_config()
    engine = create_async_engine(config.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import func, select
        
        # Scan statistics
        total_scans = await session.execute(select(func.count(Scan.id)))
        total_scans = total_scans.scalar()
        
        scans_by_status = await session.execute(
            select(Scan.status, func.count(Scan.id)).group_by(Scan.status)
        )
        scans_by_status = {row[0].value: row[1] for row in scans_by_status.all()}
        
        # Finding statistics
        total_findings = await session.execute(select(func.count(Finding.id)))
        total_findings = total_findings.scalar()
        
        findings_by_severity = await session.execute(
            select(Finding.severity, func.count(Finding.id)).group_by(Finding.severity)
        )
        findings_by_severity = {row[0].value: row[1] for row in findings_by_severity.all()}
        
        return {
            "scans": {
                "total": total_scans or 0,
                "by_status": scans_by_status,
            },
            "findings": {
                "total": total_findings or 0,
                "by_severity": findings_by_severity,
            },
        }


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    config = get_config()
    await init_db(config.get_database_url())


# Run with: uvicorn hiverecon.api.server:app --reload