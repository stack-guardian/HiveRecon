"""FastAPI router for scan result persistence and retrieval."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hiverecon.config import get_config
from hiverecon.models.scan_result import ScanResult

router = APIRouter(prefix="/api/v1/results", tags=["Results"])

config = get_config()
engine = create_async_engine(config.get_database_url(), echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    """FastAPI dependency for database session."""
    async with async_session_factory() as session:
        yield session


class ScanResultCreate(BaseModel):
    """Request body for creating a scan result."""

    scan_id: UUID
    agent_type: Literal["subdomain", "port", "endpoint", "vuln"]
    target: str = Field(..., min_length=1)
    result_data: dict[str, Any]
    severity: Literal["high", "medium", "low", "info"] = "info"


class ScanResultResponse(BaseModel):
    """Serialized scan result response."""

    id: UUID
    scan_id: UUID
    agent_type: str
    target: str
    result_data: dict[str, Any]
    severity: str
    created_at: datetime

    @classmethod
    def from_model(cls, result: ScanResult) -> "ScanResultResponse":
        return cls(
            id=result.id,
            scan_id=result.scan_id,
            agent_type=result.agent_type,
            target=result.target,
            result_data=result.result_data or {},
            severity=result.severity,
            created_at=result.created_at,
        )


@router.get("/{scan_id}", response_model=list[ScanResultResponse])
async def get_results(
    scan_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Return all stored results for a scan."""
    result = await session.execute(
        select(ScanResult)
        .where(ScanResult.scan_id == scan_id)
        .order_by(ScanResult.created_at.desc())
    )
    records = result.scalars().all()
    return [ScanResultResponse.from_model(record) for record in records]


@router.get("/{scan_id}/high", response_model=list[ScanResultResponse])
async def get_high_severity_results(
    scan_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Return only high severity results for a scan."""
    result = await session.execute(
        select(ScanResult)
        .where(ScanResult.scan_id == scan_id, ScanResult.severity == "high")
        .order_by(ScanResult.created_at.desc())
    )
    records = result.scalars().all()
    return [ScanResultResponse.from_model(record) for record in records]


@router.post("/", response_model=ScanResultResponse)
async def create_result(
    payload: ScanResultCreate,
    session: AsyncSession = Depends(get_db),
):
    """Create and persist a new scan result row."""
    record = ScanResult(
        scan_id=payload.scan_id,
        agent_type=payload.agent_type,
        target=payload.target,
        result_data=payload.result_data,
        severity=payload.severity,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return ScanResultResponse.from_model(record)
