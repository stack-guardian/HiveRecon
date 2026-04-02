from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json
import asyncio
import logging
from typing import Optional

# Using absolute imports assuming hiverecon is in PYTHONPATH
from hiverecon.database import Scan, Finding, ScanStatus, get_session
from hiverecon.core.event_bus import event_bus

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/scan/{scan_id}")
async def scan_progress_ws(
    websocket: WebSocket,
    scan_id: str,
    # Note: Depends(get_session) might not work directly in websocket if it's a generator
    # We might need to manually handle session if needed, but we'll try to get it once.
):
    await websocket.accept()
    logger.info(f"WebSocket connected for scan {scan_id}")
    
    try:
        # 1. Emit current state from DB on connect
        # We need a session. Since get_session is a generator, we use it as a context manager if possible
        # or just use the database engine directly. 
        # For simplicity in this deliverable, we'll assume a way to get the session.
        from hiverecon.config import get_config
        from sqlalchemy.ext.asyncio import create_async_engine, sessionmaker
        
        config = get_config()
        engine = create_async_engine(config.database.url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            stmt = select(Scan).where(Scan.id == scan_id)
            result = await session.execute(stmt)
            scan = result.scalar_one_or_none()
            
            if scan:
                # Count findings
                count_stmt = select(func.count(Finding.id)).where(Finding.scan_id == scan_id)
                count_result = await session.execute(count_stmt)
                findings_count = count_result.scalar()
                
                initial_state = {
                    "event": "info",
                    "status": scan.status,
                    "findings_count": findings_count,
                    "target": scan.target_domain
                }
                await websocket.send_json(initial_state)
            else:
                await websocket.send_json({"event": "error", "message": "Scan not found"})
                await websocket.close()
                return

        # 2. Subscribe to real-time events
        async for event in event_bus.subscribe(scan_id):
            await websocket.send_json(event)
            
            if event.get("event") == "complete":
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for scan {scan_id}")
    except Exception as e:
        logger.error(f"WebSocket error for scan {scan_id}: {str(e)}")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
