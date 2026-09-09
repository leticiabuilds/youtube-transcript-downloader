"""Tests for SSE progress streaming."""

from __future__ import annotations

import asyncio
import json
import unittest
from typing import List
from unittest.mock import patch

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.jobs.models import Job, JobStatus
from app.jobs.store import job_store
from app.main import app
from app.transcripts import DefinitiveTranscriptError, TranscriptResult


class JobStreamTests(unittest.TestCase):
    def test_stream_replays_history_and_stops_on_done(self) -> None:
        async def run() -> None:
            job = Job(id="job1", urls=["https://youtu.be/aaaaaaaaaaa"])
            await job.publish(
                {
                    "type": "status_update",
                    "url": "https://youtu.be/aaaaaaaaaaa",
                    "status": "aguardando",
                }
            )
            await job.publish({"type": "done"})
            job.status = JobStatus.COMPLETED

            events = [event async for event in job.stream_events()]
            self.assertEqual(
                [event["type"] for event in events],
                ["status_update", "done"],
            )

        asyncio.run(run())

    def test_stream_receives_live_events(self) -> None:
        async def run() -> None:
            job = Job(id="job2", urls=["https://youtu.be/bbbbbbbbbbb"])
            collected: List[str] = []

            async def reader() -> None:
                async for event in job.stream_events():
                    collected.append(event["type"])

            reader_task = asyncio.create_task(reader())
            await asyncio.sleep(0)
            await job.publish(
                {
                    "type": "status_update",
                    "url": "https://youtu.be/bbbbbbbbbbb",
                    "status": "processando",
                }
            )
            await job.publish({"type": "done"})
            job.status = JobStatus.COMPLETED
            await asyncio.wait_for(reader_task, timeout=1)
            self.assertEqual(collected, ["status_update", "done"])

        asyncio.run(run())


class SseEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        job_store._jobs.clear()

    async def test_sse_endpoint_streams_full_contract(self) -> None:
        def fetch_fn(url: str) -> TranscriptResult:
            if url.endswith("bad"):
                raise DefinitiveTranscriptError("Video without captions")
            video_id = "ccccccccccc" if url.endswith("good") else "ddddddddddd"
            return TranscriptResult(
                url=url,
                video_id=video_id,
                filename=f"{video_id}.txt",
                content="hello transcript",
                language_code="en",
            )

        with patch(
            "app.jobs.runner.TranscriptBatchProcessor"
        ) as processor_cls:
            from app.processing import TranscriptBatchProcessor

            def processor_factory(**kwargs):  # type: ignore[no-untyped-def]
                return TranscriptBatchProcessor(
                    fetch_fn=fetch_fn,
                    worker_count=1,
                    jitter_range_ms=(0, 0),
                    random_delay_ms=lambda _low, _high: 0,
                    on_started=kwargs.get("on_started"),
                    on_succeeded=kwargs.get("on_succeeded"),
                    on_definitive_failure=kwargs.get("on_definitive_failure"),
                    on_rate_limited=kwargs.get("on_rate_limited"),
                )

            processor_cls.side_effect = processor_factory

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                create_response = await client.post(
                    "/api/process",
                    json={
                        "urls": [
                            "https://youtu.be/good",
                            "https://youtu.be/bad",
                        ]
                    },
                )
                self.assertEqual(create_response.status_code, 200)
                job_id = create_response.json()["job_id"]

                events = []
                async with client.stream(
                    "GET", f"/api/process/{job_id}/events"
                ) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(
                        "text/event-stream",
                        response.headers["content-type"],
                    )
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = json.loads(line[len("data: ") :])
                        events.append(payload)
                        if payload.get("type") == "done":
                            break

        types = [event["type"] for event in events]
        self.assertIn("done", types)
        self.assertTrue(any(event.get("status") == "aguardando" for event in events))
        self.assertTrue(
            any(
                event.get("status") == "concluido" and event.get("filename")
                for event in events
            )
        )
        self.assertTrue(
            any(
                event.get("status") == "falhou" and event.get("error")
                for event in events
            )
        )

    def test_unknown_job_returns_404(self) -> None:
        client = TestClient(app)
        response = client.get("/api/process/does-not-exist/events")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
