"""Batch transcript processing with explicit definitive vs rate-limit error paths.

Definitive failures fail one URL and let the queue continue.
Rate-limit failures cancel remaining work and raise a batch-level signal.
There is no retry/backoff on rate limit (MVP decision).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, List, Optional, Union

from app.queue import FixedWorkerQueue, QueueStats
from app.transcripts import (
    DefinitiveTranscriptError,
    RateLimitError,
    TranscriptResult,
    fetch_transcript,
)

FetchFn = Callable[[str], TranscriptResult]
StartedFn = Callable[[str], Union[None, Awaitable[None]]]
SucceededFn = Callable[[str, TranscriptResult], Union[None, Awaitable[None]]]
DefinitiveFailedFn = Callable[[str, str], Union[None, Awaitable[None]]]
RateLimitedFn = Callable[[str], Union[None, Awaitable[None]]]


@dataclass
class BatchResult:
    stats: QueueStats
    succeeded: List[TranscriptResult] = field(default_factory=list)
    definitive_failures: List[tuple[str, str]] = field(default_factory=list)
    rate_limited: bool = False
    rate_limit_message: Optional[str] = None


class TranscriptBatchProcessor:
    """Run URLs through the fixed-worker queue with separated error handling."""

    RATE_LIMIT_MESSAGE = (
        "Rate limit do YouTube atingido. Tente novamente mais tarde."
    )

    def __init__(
        self,
        *,
        fetch_fn: FetchFn = fetch_transcript,
        worker_count: int = 3,
        jitter_range_ms: tuple[int, int] = (500, 1500),
        on_started: Optional[StartedFn] = None,
        on_succeeded: Optional[SucceededFn] = None,
        on_definitive_failure: Optional[DefinitiveFailedFn] = None,
        on_rate_limited: Optional[RateLimitedFn] = None,
        random_delay_ms: Optional[Callable[[int, int], float]] = None,
    ) -> None:
        self._fetch_fn = fetch_fn
        self._worker_count = worker_count
        self._jitter_range_ms = jitter_range_ms
        self._on_started = on_started
        self._on_succeeded = on_succeeded
        self._on_definitive_failure = on_definitive_failure
        self._on_rate_limited = on_rate_limited
        self._random_delay_ms = random_delay_ms

    async def run(self, urls: List[str]) -> BatchResult:
        result = BatchResult(
            stats=QueueStats(processed=0, succeeded=0, failed=0, cancelled=0)
        )
        queue_ref: dict[str, FixedWorkerQueue[str, TranscriptResult]] = {}

        def process_item(url: str) -> TranscriptResult:
            # DefinitiveTranscriptError and RateLimitError propagate unchanged so
            # the failed handler can branch on type without string matching.
            return self._fetch_fn(url)

        async def handle_started(url: str) -> None:
            await _emit(self._on_started, url)

        async def handle_succeeded(url: str, transcript: TranscriptResult) -> None:
            result.succeeded.append(transcript)
            await _emit(self._on_succeeded, url, transcript)

        async def handle_failed(url: str, exc: Exception) -> None:
            if isinstance(exc, RateLimitError):
                await self._handle_rate_limit(exc, queue_ref, result)
                return

            if isinstance(exc, DefinitiveTranscriptError):
                message = exc.message
            else:
                message = f"Unexpected error while fetching transcript: {exc}"

            result.definitive_failures.append((url, message))
            await _emit(self._on_definitive_failure, url, message)

        queue: FixedWorkerQueue[str, TranscriptResult] = FixedWorkerQueue(
            process_item=process_item,
            worker_count=self._worker_count,
            jitter_range_ms=self._jitter_range_ms,
            on_item_started=handle_started,
            on_item_succeeded=handle_succeeded,
            on_item_failed=handle_failed,
            random_delay_ms=self._random_delay_ms,
        )
        queue_ref["queue"] = queue

        await queue.enqueue(urls)
        result.stats = await queue.run()
        return result

    async def _handle_rate_limit(
        self,
        exc: RateLimitError,
        queue_ref: dict[str, FixedWorkerQueue[str, TranscriptResult]],
        result: BatchResult,
    ) -> None:
        if result.rate_limited:
            return

        message = exc.message or self.RATE_LIMIT_MESSAGE
        result.rate_limited = True
        result.rate_limit_message = message

        queue = queue_ref.get("queue")
        if queue is not None:
            queue.request_cancel()

        await _emit(self._on_rate_limited, message)


async def _emit(
    callback: Optional[Callable[..., Union[None, Awaitable[None]]]],
    *args: object,
) -> None:
    if callback is None:
        return
    outcome = callback(*args)
    if asyncio.iscoroutine(outcome):
        await outcome
