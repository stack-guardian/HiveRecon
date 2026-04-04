# Claude Desktop MCP config (stdio transport):
# {
#   "mcpServers": {
#     "hiverecon": {
#       "command": "/home/vibhxr/hiverecon/venv/bin/python",
#       "args": ["-m", "app.mcp.server"],
#       "cwd": "/home/vibhxr/hiverecon",
#       "env": {
#         "DATABASE_URL": "sqlite+aiosqlite:///./hiverecon.db",
#         "GROQ_API_KEY": "gsk_your_key_here",
#         "HIVERECON_REPORTS_DIR": "/home/vibhxr/hiverecon/reports"
#       }
#     }
#   }
# }
# Any MCP-compatible client can use the same stdio command/cwd/env values.

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hiverecon.config import get_config
from hiverecon.core.hive_mind import HiveMindCoordinator
from hiverecon.database import Finding, Scan, ScanStatus, init_db


config = get_config()
engine = create_async_engine(config.get_database_url(), echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

reports_dir = Path(os.environ.get("HIVERECON_REPORTS_DIR", "/app/reports"))
reports_base_url = os.environ.get("HIVERECON_REPORTS_BASE_URL")

mcp = FastMCP(
    name="HiveRecon MCP",
    instructions=(
        "Expose HiveRecon scan orchestration, scan status, findings retrieval, "
        "and report generation to external AI agents over stdio."
    ),
)


class FindingRecord(BaseModel):
    id: int
    scan_id: str
    agent_type: str
    finding_type: str
    severity: str
    title: str
    description: str | None = None
    location: str | None = None
    ai_analysis: dict[str, Any] | None = None
    educational_content: str | None = None
    created_at: datetime


class ScanStatusPayload(BaseModel):
    status: str
    pct: int
    stage: str


class ReportPayload(BaseModel):
    download_url: str


@dataclass
class ProgressState:
    status: str
    pct: int
    stage: str


_db_initialized = False
_db_lock = asyncio.Lock()
_scan_tasks: dict[str, asyncio.Task[None]] = {}
_scan_progress: dict[str, ProgressState] = {}


async def ensure_database() -> None:
    global _db_initialized

    if _db_initialized:
        return

    async with _db_lock:
        if _db_initialized:
            return
        await init_db(config.get_database_url())
        _db_initialized = True


def parse_scan_id(scan_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(scan_id)
    except ValueError as exc:
        raise ValueError(f"Invalid scan_id: {scan_id}") from exc


def report_download_url(path: Path) -> str:
    if reports_base_url:
        return f"{reports_base_url.rstrip('/')}/{path.name}"
    return path.resolve().as_uri()


def serialize_finding(finding: Finding) -> FindingRecord:
    return FindingRecord(
        id=finding.id,
        scan_id=str(finding.scan_id),
        agent_type=finding.agent_type.value,
        finding_type=finding.finding_type,
        severity=finding.severity.value,
        title=finding.title,
        description=finding.description,
        location=finding.location,
        ai_analysis=finding.ai_analysis,
        educational_content=finding.educational_content,
        created_at=finding.created_at,
    )


def render_report(
    scan: Scan,
    findings: list[FindingRecord],
    output_format: str,
) -> str:
    payload = {
        "scan_id": str(scan.id),
        "target": scan.target_domain,
        "status": scan.status.value,
        "platform": scan.platform,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "total_findings": len(findings),
        "findings": [finding.model_dump(mode="json") for finding in findings],
    }

    if output_format == "json":
        return json.dumps(payload, indent=2)

    if output_format == "markdown":
        lines = [
            f"# HiveRecon Report: {scan.target_domain}",
            "",
            f"- Scan ID: `{scan.id}`",
            f"- Status: `{scan.status.value}`",
            f"- Findings: `{len(findings)}`",
            "",
            "## Findings",
        ]
        if not findings:
            lines.append("")
            lines.append("No findings recorded for this scan.")
            return "\n".join(lines)

        for finding in findings:
            lines.extend(
                [
                    "",
                    f"### {finding.title}",
                    f"- Severity: `{finding.severity}`",
                    f"- Type: `{finding.finding_type}`",
                    f"- Location: `{finding.location or 'n/a'}`",
                    f"- Description: {finding.description or 'n/a'}",
                ]
            )
        return "\n".join(lines)

    if output_format == "text":
        lines = [
            f"HiveRecon report for {scan.target_domain}",
            f"Scan ID: {scan.id}",
            f"Status: {scan.status.value}",
            f"Total findings: {len(findings)}",
            "",
            "Findings:",
        ]
        if not findings:
            lines.append("  - No findings recorded.")
            return "\n".join(lines)

        for finding in findings:
            lines.append(
                f"  - [{finding.severity}] {finding.title} "
                f"({finding.finding_type}) @ {finding.location or 'n/a'}"
            )
        return "\n".join(lines)

    raise ValueError("Unsupported format. Use one of: json, markdown, text")


async def persist_scan_findings(
    session: AsyncSession,
    scan_uuid: uuid.UUID,
    findings: list[Finding],
) -> None:
    for finding in findings:
        finding.id = None
        finding.scan_id = scan_uuid
        session.add(finding)


async def execute_scan(scan_uuid: uuid.UUID, target: str, scan_type: str) -> None:
    scan_key = str(scan_uuid)
    _scan_progress[scan_key] = ProgressState(status="running", pct=10, stage="initializing")

    async with session_factory() as session:
        scan = await session.get(Scan, scan_uuid)
        if scan is None:
            _scan_progress[scan_key] = ProgressState(status="failed", pct=100, stage="missing_scan")
            return
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        await session.commit()

    try:
        _scan_progress[scan_key] = ProgressState(status="running", pct=25, stage="recon")
        coordinator = HiveMindCoordinator(scan_id=str(scan_uuid), config=config)
        findings, summary = await coordinator.run_scan(
            target=target,
            scan_id=str(scan_uuid),
            scope_config={"scan_type": scan_type},
        )

        _scan_progress[scan_key] = ProgressState(status="running", pct=85, stage="persisting_findings")
        async with session_factory() as session:
            await persist_scan_findings(session, scan_uuid, findings)
            scan = await session.get(Scan, scan_uuid)
            if scan is not None:
                scan.summary = summary
                scan.status = ScanStatus.COMPLETED
                scan.completed_at = datetime.utcnow()
            await session.commit()

        _scan_progress[scan_key] = ProgressState(status="completed", pct=100, stage="completed")
    except Exception as exc:
        async with session_factory() as session:
            scan = await session.get(Scan, scan_uuid)
            if scan is not None:
                scan.status = ScanStatus.FAILED
                scan.error_message = str(exc)
                scan.completed_at = datetime.utcnow()
                await session.commit()

        _scan_progress[scan_key] = ProgressState(status="failed", pct=100, stage="failed")
    finally:
        _scan_tasks.pop(scan_key, None)


@mcp.tool(
    name="start_scan",
    description="Start a new HiveRecon scan and return the generated scan ID.",
)
async def start_scan(
    target: Annotated[
        str,
        Field(description="Target hostname, domain, or URL that HiveRecon should scan."),
    ],
    scan_type: Annotated[
        str,
        Field(description="Scan profile identifier such as full, passive, or quick."),
    ],
) -> str:
    await ensure_database()

    normalized_target = target.strip()
    normalized_scan_type = scan_type.strip().lower()
    if not normalized_target:
        raise ValueError("target must not be empty")
    if not normalized_scan_type:
        raise ValueError("scan_type must not be empty")

    scan_uuid = uuid.uuid4()
    scan = Scan(
        id=scan_uuid,
        target_domain=normalized_target,
        scope_config={"scan_type": normalized_scan_type},
        status=ScanStatus.PENDING,
    )

    async with session_factory() as session:
        session.add(scan)
        await session.commit()

    scan_key = str(scan_uuid)
    _scan_progress[scan_key] = ProgressState(status="pending", pct=0, stage="queued")
    _scan_tasks[scan_key] = asyncio.create_task(
        execute_scan(scan_uuid=scan_uuid, target=normalized_target, scan_type=normalized_scan_type)
    )
    return scan_key


@mcp.tool(
    name="get_scan_status",
    description="Return the current status, completion percentage, and stage for a scan.",
    structured_output=True,
)
async def get_scan_status(
    scan_id: Annotated[
        str,
        Field(description="UUID of the HiveRecon scan to inspect."),
    ],
) -> ScanStatusPayload:
    await ensure_database()
    scan_uuid = parse_scan_id(scan_id)

    progress = _scan_progress.get(scan_id)
    if progress is not None:
        return ScanStatusPayload(status=progress.status, pct=progress.pct, stage=progress.stage)

    async with session_factory() as session:
        scan = await session.get(Scan, scan_uuid)
        if scan is None:
            raise ValueError(f"Scan not found: {scan_id}")

    fallback = {
        ScanStatus.PENDING: ProgressState("pending", 0, "queued"),
        ScanStatus.RUNNING: ProgressState("running", 50, "recon"),
        ScanStatus.COMPLETED: ProgressState("completed", 100, "completed"),
        ScanStatus.FAILED: ProgressState("failed", 100, "failed"),
        ScanStatus.CANCELLED: ProgressState("cancelled", 100, "cancelled"),
    }[scan.status]
    return ScanStatusPayload(status=fallback.status, pct=fallback.pct, stage=fallback.stage)


@mcp.tool(
    name="get_findings",
    description="Return findings for a scan, optionally filtered by severity.",
    structured_output=True,
)
async def get_findings(
    scan_id: Annotated[
        str,
        Field(description="UUID of the HiveRecon scan whose findings should be returned."),
    ],
    severity: Annotated[
        str | None,
        Field(description="Optional severity filter: critical, high, medium, low, or info."),
    ] = None,
) -> list[FindingRecord]:
    await ensure_database()
    scan_uuid = parse_scan_id(scan_id)

    async with session_factory() as session:
        query = select(Finding).where(Finding.scan_id == scan_uuid).order_by(Finding.created_at.desc())
        if severity:
            query = query.where(Finding.severity == severity.lower())
        result = await session.execute(query)
        findings = result.scalars().all()

    return [serialize_finding(finding) for finding in findings]


@mcp.tool(
    name="generate_report",
    description="Generate a report artifact for a completed scan and return its download URL.",
    structured_output=True,
)
async def generate_report(
    scan_id: Annotated[
        str,
        Field(description="UUID of the HiveRecon scan to export."),
    ],
    format: Annotated[
        str,
        Field(description="Report format: json, markdown, or text."),
    ],
) -> ReportPayload:
    await ensure_database()
    scan_uuid = parse_scan_id(scan_id)
    output_format = format.strip().lower()

    async with session_factory() as session:
        scan = await session.get(Scan, scan_uuid)
        if scan is None:
            raise ValueError(f"Scan not found: {scan_id}")

        findings_result = await session.execute(
            select(Finding).where(Finding.scan_id == scan_uuid).order_by(Finding.created_at.desc())
        )
        finding_rows = findings_result.scalars().all()

    findings = [serialize_finding(finding) for finding in finding_rows]
    reports_dir.mkdir(parents=True, exist_ok=True)

    suffix_map = {"json": "json", "markdown": "md", "text": "txt"}
    if output_format not in suffix_map:
        raise ValueError("Unsupported format. Use one of: json, markdown, text")

    report_path = reports_dir / f"{scan_id}.{suffix_map[output_format]}"
    report_path.write_text(render_report(scan, findings, output_format), encoding="utf-8")

    return ReportPayload(download_url=report_download_url(report_path))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
