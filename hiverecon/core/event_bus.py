import asyncio
from typing import AsyncGenerator, Dict, List
import logging

logger = logging.getLogger(__name__)


class ScanEventBus:
    """Async event bus used to broadcast scan progress updates via queues."""

    def __init__(self):
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, scan_id: str) -> AsyncGenerator[dict, None]:
        queue = asyncio.Queue()
        async with self._lock:
            self.subscribers.setdefault(scan_id, []).append(queue)

        try:
            while True:
                event = await queue.get()
                if event is None:  # sentinel
                    break
                yield event
        finally:
            async with self._lock:
                queues = self.subscribers.get(scan_id, [])
                if queue in queues:
                    queues.remove(queue)
                    if not queues:
                        self.subscribers.pop(scan_id, None)

    async def publish(self, scan_id: str, event_dict: dict):
        async with self._lock:
            for queue in self.subscribers.get(scan_id, []):
                await queue.put(event_dict)

    async def close_scan(self, scan_id: str):
        async with self._lock:
            for queue in self.subscribers.get(scan_id, []):
                await queue.put(None)


event_bus = ScanEventBus()
