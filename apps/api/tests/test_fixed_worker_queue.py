"""Unit tests for FixedWorkerQueue. Run: python -m unittest tests.test_fixed_worker_queue"""

from __future__ import annotations

import asyncio
import time
import unittest
from typing import List

from app.queue import FixedWorkerQueue


class FixedWorkerQueueTests(unittest.TestCase):
    def test_processes_all_items_with_injected_handler(self) -> None:
        seen: List[int] = []

        def process_item(item: int) -> int:
            seen.append(item)
            return item * 2

        async def run() -> None:
            queue: FixedWorkerQueue[int, int] = FixedWorkerQueue(
                process_item=process_item,
                worker_count=2,
                jitter_range_ms=(0, 0),
                random_delay_ms=lambda _low, _high: 0,
            )
            await queue.enqueue([1, 2, 3, 4])
            stats = await queue.run()
            self.assertEqual(stats.succeeded, 4)
            self.assertEqual(stats.failed, 0)
            self.assertEqual(sorted(seen), [1, 2, 3, 4])

        asyncio.run(run())

    def test_applies_jitter_before_processing(self) -> None:
        delays: List[float] = []
        started_at: List[float] = []

        def process_item(item: str) -> str:
            started_at.append(time.monotonic())
            return item

        async def run() -> None:
            queue: FixedWorkerQueue[str, str] = FixedWorkerQueue(
                process_item=process_item,
                worker_count=1,
                jitter_range_ms=(40, 40),
                random_delay_ms=lambda low, high: float(low),
            )
            await queue.enqueue(["a"])
            before = time.monotonic()
            await queue.run()
            delays.append(started_at[0] - before)

        asyncio.run(run())
        self.assertGreaterEqual(delays[0], 0.035)

    def test_bounds_concurrency_to_worker_count(self) -> None:
        current = 0
        max_seen = 0

        async def run() -> None:
            nonlocal current, max_seen
            lock = asyncio.Lock()

            async def process_item(item: int) -> int:
                nonlocal current, max_seen
                async with lock:
                    current += 1
                    max_seen = max(max_seen, current)
                await asyncio.sleep(0.05)
                async with lock:
                    current -= 1
                return item

            queue: FixedWorkerQueue[int, int] = FixedWorkerQueue(
                process_item=process_item,
                worker_count=3,
                jitter_range_ms=(0, 0),
                random_delay_ms=lambda _low, _high: 0,
            )
            await queue.enqueue(list(range(9)))
            stats = await queue.run()
            self.assertEqual(stats.succeeded, 9)
            self.assertLessEqual(max_seen, 3)

        asyncio.run(run())

    def test_request_cancel_skips_remaining_items(self) -> None:
        processed: List[int] = []

        async def process_item(item: int) -> int:
            processed.append(item)
            if item == 1:
                queue.request_cancel()
            await asyncio.sleep(0.02)
            return item

        queue: FixedWorkerQueue[int, int]

        async def run() -> None:
            nonlocal queue
            queue = FixedWorkerQueue(
                process_item=process_item,
                worker_count=1,
                jitter_range_ms=(0, 0),
                random_delay_ms=lambda _low, _high: 0,
            )
            await queue.enqueue([1, 2, 3, 4, 5])
            stats = await queue.run()
            self.assertEqual(stats.succeeded, 1)
            self.assertGreaterEqual(stats.cancelled, 1)
            self.assertEqual(processed, [1])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
