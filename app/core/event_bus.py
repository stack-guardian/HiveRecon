import asyncio
from typing import AsyncGenerator, Dict, List
import json
import logging

logger = logging.getLogger(__name__)

class ScanEventBus:
    """
    In-process async event bus for scan progress updates.
    Uses asyncio.Queue to decouple publishers from subscribers.
    """
    def __init__(self):
        # map scan_id -> list of queues
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, scan_id: str) -> AsyncGenerator[dict, None]:
        """Subscribe to events for a specific scan_id."""
        queue = asyncio.Queue()
        async with self._lock:
            if scan_id not in self.subscribers:
                self.subscribers[scan_id] = []
            self.subscribers[scan_id].append(queue)
        
        try:
            while True:
                event = await queue.get()
                if event is None: # Sentinel for completion/close
                    break
                yield event
        finally:
            async with self._lock:
                if scan_id in self.subscribers:
                    self.subscribers[scan_id].remove(queue)
                    if not self.subscribers[scan_id]:
                        del self.subscribers[scan_id]

    async def publish(self, scan_id: str, event_dict: dict):
        """Publish an event to all subscribers of a scan_id."""
        async with self._lock:
            if scan_id in self.subscribers:
                # Use asyncio.gather to push to all queues without blocking each other
                # though Queue.put_nowait is also an option if we don't care about backpressure
                for queue in self.subscribers[scan_id]:
                    await queue.put(event_dict)

    async def close_scan(self, scan_id: str):
        """Send sentinel to all subscribers to close their generators."""
        async with self._lock:
            if scan_id in self.subscribers:
                for queue in self.subscribers[scan_id]:
                    await queue.put(None)

# Global instance
event_bus = ScanEventBus()
