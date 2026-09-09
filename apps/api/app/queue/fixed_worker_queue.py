"""In-memory fixed-worker queue with request jitter.

Keeps concurrency bounded (default 3 workers) and spaces work with a random
delay before each item starts. Processing logic is injected so this module
stays independent from FastAPI routes and the transcript extractor.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, List, Optional, TypeVar, Union

T = TypeVar("T")
R = TypeVar("R")

ProcessFn = Callable[[T], Union[R, Awaitable[R]]]
StartedFn = Callable[[T], Union[None, Awaitable[None]]]
SucceededFn = Callable[[T, R], Union[None, Awaitable[None]]]
FailedFn = Callable[[T, Exception], Union[None, Awaitable[None]]]


@dataclass(frozen=True)
class QueueStats:
    processed: int
    succeeded: int
    failed: int
    cancelled: int


class FixedWorkerQueue(Generic[T, R]):
    """Consume queued items with a fixed worker pool and start-of-item jitter."""

    def __init__(
        self,
        *,
        process_item: ProcessFn[T, R],
        worker_count: int = 3,
        jitter_range_ms: tuple[int, int] = (500, 1500),
        on_item_started: Optional[StartedFn[T]] = None,
        on_item_succeeded: Optional[SucceededFn[T, R]] = None,
        on_item_failed: Optional[FailedFn[T]] = None,
        random_delay_ms: Optional[Callable[[int, int], float]] = None,
    ) -> None:
        if worker_count < 1:
            raise ValueError("worker_count must be at least 1")
        low_ms, high_ms = jitter_range_ms
        if low_ms < 0 or high_ms < low_ms:
            raise ValueError("jitter_range_ms must satisfy 0 <= low <= high")

        self._process_item = process_item
        self._worker_count = worker_count
        self._jitter_range_ms = jitter_range_ms
        self._on_item_started = on_item_started
        self._on_item_succeeded = on_item_succeeded
        self._on_item_failed = on_item_failed
        self._random_delay_ms = random_delay_ms or random.uniform

        self._queue: asyncio.Queue[Optional[T]] = asyncio.Queue()
        self._cancel_requested = asyncio.Event()
        self._processed = 0
        self._succeeded = 0
        self._failed = 0
        self._cancelled = 0
        self._lock = asyncio.Lock()

    @property
    def worker_count(self) -> int:
        return self._worker_count

    def request_cancel(self) -> None:
        """Stop claiming new items. Items already in-flight still finish."""
        self._cancel_requested.set()

    async def enqueue(self, items: List[T]) -> None:
        for item in items:
            await self._queue.put(item)

    async def run(self) -> QueueStats:
        """Process the queue until empty or cancelled, then return stats."""
        workers = [
            asyncio.create_task(self._worker_loop(worker_id=index))
            for index in range(self._worker_count)
        ]

        await self._queue.join()

        for _ in range(self._worker_count):
            await self._queue.put(None)

        await asyncio.gather(*workers)
        return QueueStats(
            processed=self._processed,
            succeeded=self._succeeded,
            failed=self._failed,
            cancelled=self._cancelled,
        )

    async def _worker_loop(self, worker_id: int) -> None:
        del worker_id  # reserved for future logging
        while True:
            item = await self._queue.get()
            try:
                if item is None:
                    return

                if self._cancel_requested.is_set():
                    async with self._lock:
                        self._cancelled += 1
                    continue

                await self._process_one(item)
            finally:
                self._queue.task_done()

    async def _process_one(self, item: T) -> None:
        low_ms, high_ms = self._jitter_range_ms
        delay_ms = self._random_delay_ms(low_ms, high_ms)
        await asyncio.sleep(delay_ms / 1000.0)

        if self._cancel_requested.is_set():
            async with self._lock:
                self._cancelled += 1
            return

        await self._emit(self._on_item_started, item)

        try:
            result = await self._call_process(item)
        except Exception as exc:
            async with self._lock:
                self._processed += 1
                self._failed += 1
            await self._emit(self._on_item_failed, item, exc)
            return

        async with self._lock:
            self._processed += 1
            self._succeeded += 1
        await self._emit(self._on_item_succeeded, item, result)

    async def _call_process(self, item: T) -> R:
        if asyncio.iscoroutinefunction(self._process_item):
            return await self._process_item(item)

        return await asyncio.to_thread(self._process_item, item)

    async def _emit(
        self,
        callback: Optional[Callable[..., Union[None, Awaitable[None]]]],
        *args: object,
    ) -> None:
        if callback is None:
            return
        outcome = callback(*args)
        if asyncio.iscoroutine(outcome):
            await outcome
