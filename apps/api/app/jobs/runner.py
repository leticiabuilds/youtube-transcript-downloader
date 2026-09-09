"""Start batch processing for a job and publish progress events."""

from __future__ import annotations

import logging

from app.jobs.models import Job, JobStatus
from app.processing import TranscriptBatchProcessor
from app.transcripts import TranscriptResult

logger = logging.getLogger(__name__)


async def run_job(job: Job) -> None:
    job.status = JobStatus.RUNNING

    for url in job.urls:
        await job.publish(
            {"type": "status_update", "url": url, "status": "aguardando"}
        )

    async def on_started(url: str) -> None:
        await job.publish(
            {"type": "status_update", "url": url, "status": "processando"}
        )

    async def on_succeeded(url: str, transcript: TranscriptResult) -> None:
        await job.publish(
            {
                "type": "status_update",
                "url": url,
                "status": "concluido",
                "filename": transcript.filename,
                "content": transcript.content,
            }
        )

    async def on_definitive_failure(url: str, message: str) -> None:
        await job.publish(
            {
                "type": "status_update",
                "url": url,
                "status": "falhou",
                "error": message,
            }
        )

    async def on_rate_limited(message: str) -> None:
        await job.publish({"type": "rate_limited", "message": message})

    processor = TranscriptBatchProcessor(
        on_started=on_started,
        on_succeeded=on_succeeded,
        on_definitive_failure=on_definitive_failure,
        on_rate_limited=on_rate_limited,
    )

    try:
        await processor.run(job.urls)
    except Exception:
        logger.exception("Unhandled error while running job %s", job.id)
    finally:
        await job.publish({"type": "done"})
        job.status = JobStatus.COMPLETED
        await job.close_events()
