"""Tests for definitive vs rate-limit error handling in batch processing."""

from __future__ import annotations

import asyncio
import unittest
from typing import List

from app.processing import TranscriptBatchProcessor
from app.transcripts import (
    DefinitiveTranscriptError,
    RateLimitError,
    TranscriptResult,
)


def _ok(url: str) -> TranscriptResult:
    video_id = url.rstrip("/").split("/")[-1]
    return TranscriptResult(
        url=url,
        video_id=video_id,
        filename=f"{video_id}.txt",
        content=f"transcript for {video_id}",
        language_code="en",
    )


class TranscriptBatchProcessorTests(unittest.TestCase):
    def test_definitive_failure_continues_queue(self) -> None:
        calls: List[str] = []
        definitive: List[tuple[str, str]] = []

        def fetch_fn(url: str) -> TranscriptResult:
            calls.append(url)
            if url.endswith("bad"):
                raise DefinitiveTranscriptError("Video without captions")
            return _ok(url)

        async def run() -> None:
            processor = TranscriptBatchProcessor(
                fetch_fn=fetch_fn,
                worker_count=1,
                jitter_range_ms=(0, 0),
                random_delay_ms=lambda _low, _high: 0,
                on_definitive_failure=lambda url, message: definitive.append(
                    (url, message)
                ),
            )
            result = await processor.run(
                [
                    "https://youtu.be/good1",
                    "https://youtu.be/bad",
                    "https://youtu.be/good2",
                ]
            )
            self.assertFalse(result.rate_limited)
            self.assertEqual(len(result.succeeded), 2)
            self.assertEqual(len(result.definitive_failures), 1)
            self.assertEqual(definitive[0][1], "Video without captions")
            self.assertEqual(result.stats.cancelled, 0)
            self.assertEqual(len(calls), 3)

        asyncio.run(run())

    def test_rate_limit_cancels_remaining_items(self) -> None:
        calls: List[str] = []
        rate_messages: List[str] = []
        definitive: List[tuple[str, str]] = []

        def fetch_fn(url: str) -> TranscriptResult:
            calls.append(url)
            if url.endswith("blocked"):
                raise RateLimitError("simulated youtube block")
            return _ok(url)

        async def run() -> None:
            processor = TranscriptBatchProcessor(
                fetch_fn=fetch_fn,
                worker_count=1,
                jitter_range_ms=(0, 0),
                random_delay_ms=lambda _low, _high: 0,
                on_definitive_failure=lambda url, message: definitive.append(
                    (url, message)
                ),
                on_rate_limited=lambda message: rate_messages.append(message),
            )
            result = await processor.run(
                [
                    "https://youtu.be/ok1",
                    "https://youtu.be/blocked",
                    "https://youtu.be/ok2",
                    "https://youtu.be/ok3",
                ]
            )
            self.assertTrue(result.rate_limited)
            self.assertEqual(result.rate_limit_message, "simulated youtube block")
            self.assertEqual(rate_messages, ["simulated youtube block"])
            self.assertEqual(len(result.succeeded), 1)
            self.assertEqual(definitive, [])
            self.assertEqual(result.definitive_failures, [])
            self.assertGreaterEqual(result.stats.cancelled, 1)
            self.assertEqual(calls, ["https://youtu.be/ok1", "https://youtu.be/blocked"])

        asyncio.run(run())

    def test_rate_limit_and_definitive_paths_do_not_mix(self) -> None:
        definitive_events: List[str] = []
        rate_limit_events: List[str] = []

        def fetch_fn(url: str) -> TranscriptResult:
            if "rate" in url:
                raise RateLimitError("blocked")
            if "fail" in url:
                raise DefinitiveTranscriptError("no captions")
            return _ok(url)

        async def run() -> None:
            processor = TranscriptBatchProcessor(
                fetch_fn=fetch_fn,
                worker_count=1,
                jitter_range_ms=(0, 0),
                random_delay_ms=lambda _low, _high: 0,
                on_definitive_failure=lambda url, _message: definitive_events.append(
                    url
                ),
                on_rate_limited=lambda message: rate_limit_events.append(message),
            )
            result = await processor.run(
                [
                    "https://youtu.be/fail",
                    "https://youtu.be/ok",
                    "https://youtu.be/rate",
                    "https://youtu.be/never",
                ]
            )
            self.assertEqual(definitive_events, ["https://youtu.be/fail"])
            self.assertEqual(rate_limit_events, ["blocked"])
            self.assertEqual(len(result.succeeded), 1)
            self.assertTrue(result.rate_limited)
            self.assertNotIn("https://youtu.be/rate", definitive_events)
            self.assertNotIn("https://youtu.be/never", definitive_events)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
