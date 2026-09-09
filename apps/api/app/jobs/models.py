"""In-memory job models and event payloads for transcript processing."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass
class Job:
    id: str
    urls: List[str]
    status: JobStatus = JobStatus.PENDING
    events: asyncio.Queue[Optional[Dict[str, Any]]] = field(
        default_factory=asyncio.Queue
    )
    event_history: List[Dict[str, Any]] = field(default_factory=list)

    async def publish(self, event: Dict[str, Any]) -> None:
        self.event_history.append(event)
        await self.events.put(event)

    async def close_events(self) -> None:
        await self.events.put(None)
