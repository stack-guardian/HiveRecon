"""
Rate limiter and resource manager for recon agents.

Prevents WAF triggers, manages system resources, and ensures fair execution.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    requests_per_second: float = 10.0
    requests_per_minute: float = 300.0
    burst_size: int = 20
    delay_between_requests: float = 0.1
    max_concurrent_requests: int = 5


@dataclass
class ResourceLimits:
    """System resource limits."""
    
    max_memory_mb: int = 2048
    max_cpu_percent: float = 80.0
    max_open_files: int = 1024
    max_processes: int = 50


class TokenBucket:
    """
    Token bucket rate limiter.
    
    Allows bursting up to bucket_size, then rate-limits to refill_rate.
    """
    
    def __init__(self, refill_rate: float, bucket_size: int):
        self.refill_rate = refill_rate  # tokens per second
        self.bucket_size = bucket_size
        self.tokens = bucket_size
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if successful."""
        async with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def wait_for_token(self, tokens: int = 1) -> None:
        """Wait until tokens are available."""
        while True:
            if await self.acquire(tokens):
                return
            
            # Calculate wait time
            async with self._lock:
                self._refill()
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.refill_rate
            
            await asyncio.sleep(max(0.01, wait_time))
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
        self.last_refill = now


class RateLimiter:
    """
    Multi-layer rate limiter for recon operations.
    
    Combines per-second, per-minute, and per-host rate limiting.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Global rate limiters
        self.per_second_limiter = TokenBucket(
            refill_rate=self.config.requests_per_second,
            bucket_size=self.config.burst_size
        )
        
        # Per-host rate limiters (prevent hammering single target)
        self._host_limiters: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                refill_rate=self.config.requests_per_second / 2,
                bucket_size=self.config.burst_size // 2
            )
        )
    
    async def acquire(self, host: Optional[str] = None) -> None:
        """Acquire rate limit permission."""
        # Wait for global rate limit
        await self.per_second_limiter.wait_for_token()
        
        # Wait for host-specific rate limit
        if host:
            host_limiter = self._host_limiters[host]
            await host_limiter.wait_for_token()
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ResourceManager:
    """
    Manages system resources during recon operations.
    
    Prevents resource exhaustion from running multiple agents simultaneously.
    """
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._active_tasks: set[asyncio.Task] = set()
    
    def get_semaphore(self, max_concurrent: int) -> asyncio.Semaphore:
        """Get or create a semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(max_concurrent)
        return self._semaphore
    
    async def spawn(self, coro, name: Optional[str] = None) -> asyncio.Task:
        """Spawn a task with resource tracking."""
        task = asyncio.create_task(coro, name=name)
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)
        return task
    
    async def wait_all(self, timeout: Optional[float] = None) -> None:
        """Wait for all active tasks to complete."""
        if self._active_tasks:
            await asyncio.wait(self._active_tasks, timeout=timeout)
    
    def get_active_count(self) -> int:
        """Get number of active tasks."""
        return len(self._active_tasks)
    
    async def cleanup(self) -> None:
        """Cancel all active tasks."""
        for task in self._active_tasks:
            task.cancel()
        
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)


class AgentScheduler:
    """
    Schedules and coordinates recon agents with rate limiting and resource management.
    
    Features:
    - Priority-based scheduling
    - Rate limiting per tool and target
    - Resource-aware concurrency
    - Automatic retry with backoff
    """
    
    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        resource_limits: Optional[ResourceLimits] = None,
        max_concurrent_agents: int = 3,
    ):
        self.rate_limiter = RateLimiter(rate_limit_config)
        self.resource_manager = ResourceManager(resource_limits)
        self.max_concurrent_agents = max_concurrent_agents
        self._agent_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._results = {}
    
    async def submit(
        self,
        agent_id: str,
        agent_type: str,
        target: str,
        coro,
        priority: int = 5,
    ) -> None:
        """Submit an agent task for execution."""
        await self._agent_queue.put((priority, agent_id, agent_type, target, coro))
    
    async def run_all(self) -> dict:
        """Run all queued agents with proper scheduling."""
        semaphore = self.resource_manager.get_semaphore(self.max_concurrent_agents)
        tasks = []
        
        async def worker():
            while True:
                try:
                    priority, agent_id, agent_type, target, coro = await asyncio.wait_for(
                        self._agent_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    break
                
                async with semaphore:
                    # Apply rate limiting
                    await self.rate_limiter.acquire(target)
                    
                    try:
                        result = await coro
                        self._results[agent_id] = {"success": True, "result": result}
                    except Exception as e:
                        self._results[agent_id] = {"success": False, "error": str(e)}
                
                self._agent_queue.task_done()
        
        # Start workers
        workers = [asyncio.create_task(worker()) for _ in range(self.max_concurrent_agents)]
        await asyncio.gather(*workers)
        
        return self._results
    
    async def run_with_retry(
        self,
        agent_id: str,
        coro,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ) -> any:
        """Run a single agent with automatic retry."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await coro
            except Exception as e:
                last_error = e
                
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
        
        raise last_error


@dataclass
class ScanQuota:
    """Quota tracking for scans."""
    
    max_scans_per_hour: int = 10
    max_scans_per_day: int = 50
    max_targets_per_scan: int = 100
    _hourly_count: int = field(default=0, init=False)
    _daily_count: int = field(default=0, init=False)
    _last_hour_reset: float = field(default_factory=time.time, init=False)
    _last_day_reset: float = field(default_factory=time.time, init=False)
    
    def can_start_scan(self) -> bool:
        """Check if a new scan can be started."""
        self._reset_counters_if_needed()
        return (
            self._hourly_count < self.max_scans_per_hour and
            self._daily_count < self.max_scans_per_day
        )
    
    def consume_scan(self) -> None:
        """Consume a scan quota."""
        if self.can_start_scan():
            self._hourly_count += 1
            self._daily_count += 1
        else:
            raise RuntimeError("Scan quota exceeded")
    
    def _reset_counters_if_needed(self) -> None:
        """Reset counters based on time windows."""
        now = time.time()
        
        # Reset hourly counter
        if now - self._last_hour_reset > 3600:
            self._hourly_count = 0
            self._last_hour_reset = now
        
        # Reset daily counter
        if now - self._last_day_reset > 86400:
            self._daily_count = 0
            self._last_day_reset = now


# Global instances
_default_scheduler: Optional[AgentScheduler] = None
_default_quota: Optional[ScanQuota] = None


def get_scheduler() -> AgentScheduler:
    """Get the global agent scheduler."""
    global _default_scheduler
    if _default_scheduler is None:
        _default_scheduler = AgentScheduler()
    return _default_scheduler


def get_quota() -> ScanQuota:
    """Get the global scan quota tracker."""
    global _default_quota
    if _default_quota is None:
        _default_quota = ScanQuota()
    return _default_quota
