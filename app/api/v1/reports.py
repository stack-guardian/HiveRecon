"""FastAPI router for report generation endpoints.

Provides endpoints to generate and download scan reports in PDF and Markdown formats.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from hiverecon.database import Scan
from hiverecon.reports.generator import ReportGenerator
from hiverecon.config import get_config


router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])
config = get_config()

# Database setup for reports module
_engine = create_async_engine(config.get_database_url(), echo=False)
_async_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Get async database session for reports endpoints.
    
    Returns:
        AsyncSession: Database session.
    """
    async with _async_session_factory() as session:
        yield session


@router.get("/{scan_id}/markdown")
async def get_markdown_report(
    scan_id: str,
    session: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Generate and download a Markdown report for the specified scan.
    
    Args:
        scan_id: The UUID of the scan to generate a report for.
        session: Async database session dependency.
    
    Returns:
        FileResponse with the generated Markdown report.
    
    Raises:
        HTTPException: 404 if scan not found, 500 if generation fails.
    """
    scan = await session.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    try:
        generator = ReportGenerator()
        report_path = await generator.generate(scan_id, format="markdown")
        
        return FileResponse(
            path=report_path,
            media_type="text/markdown",
            filename=report_path.name,
            headers={
                "Content-Disposition": f'attachment; filename="{report_path.name}"'
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/{scan_id}/pdf")
async def get_pdf_report(
    scan_id: str,
    session: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Generate and download a PDF report for the specified scan.
    
    Args:
        scan_id: The UUID of the scan to generate a report for.
        session: Async database session dependency.
    
    Returns:
        FileResponse with the generated PDF report.
    
    Raises:
        HTTPException: 404 if scan not found, 500 if generation fails.
    """
    scan = await session.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    try:
        generator = ReportGenerator()
        report_path = await generator.generate(scan_id, format="pdf")
        
        return FileResponse(
            path=report_path,
            media_type="application/pdf",
            filename=report_path.name,
            headers={
                "Content-Disposition": f'attachment; filename="{report_path.name}"'
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/{scan_id}")
async def get_report_info(
    scan_id: str,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Get metadata about available reports for a scan.
    
    Args:
        scan_id: The UUID of the scan.
        session: Async database session dependency.
    
    Returns:
        Dictionary with report availability information.
    
    Raises:
        HTTPException: 404 if scan not found.
    """
    scan = await session.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    reports_dir = config.data_dir / "reports"
    
    available_reports = []
    if reports_dir.exists():
        for pattern in ["pdf", "md"]:
            for report_file in reports_dir.glob(f"report_{scan_id[:8]}*.{pattern}"):
                available_reports.append({
                    "filename": report_file.name,
                    "format": "pdf" if pattern == "pdf" else "markdown",
                    "size_bytes": report_file.stat().st_size,
                    "path": str(report_file),
                })
    
    return {
        "scan_id": scan_id,
        "scan_status": scan.status.value if scan.status else "unknown",
        "reports": available_reports,
        "download_urls": {
            "markdown": f"/api/v1/reports/{scan_id}/markdown",
            "pdf": f"/api/v1/reports/{scan_id}/pdf",
        },
    }
