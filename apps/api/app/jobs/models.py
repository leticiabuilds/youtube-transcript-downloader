"""In-memory job models and event payloads for transcript processing."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass
class Job:
    id: str
    urls: List[str]
    status: JobStatus = JobStatus.PENDING
    event_history: List[Dict[str, Any]] = field(default_factory=list)
    _waiters: List[asyncio.Event] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def publish(self, event: Dict[str, Any]) -> None:
        async with self._lock:
            self.event_history.append(event)
            waiters = list(self._waiters)
        for waiter in waiters:
            waiter.set()

    async def stream_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Yield historical events, then live events, until type == done."""
        index = 0
        while True:
            async with self._lock:
                snapshot = list(self.event_history)
                done = self.status == JobStatus.COMPLETED and index >= len(snapshot)

            while index < len(snapshot):
                event = snapshot[index]
                index += 1
                yield event
                if event.get("type") == "done":
                    return

            if done:
                return

            waiter = asyncio.Event()
            async with self._lock:
                if index < len(self.event_history):
                    continue
                self._waiters.append(waiter)
            try:
                await waiter.wait()
            finally:
                async with self._lock:
                    if waiter in self._waiters:
                        self._waiters.remove(waiter)
