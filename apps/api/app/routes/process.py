"""HTTP routes for starting transcript processing jobs and streaming progress."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, List, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.jobs import job_store, run_job
from app.transcripts import resolve_language_codes

router = APIRouter(prefix="/api")


class ProcessRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1)
    language: Literal["en", "pt"] = "en"

    @field_validator("urls")
    @classmethod
    def normalize_and_require_urls(cls, value: List[str]) -> List[str]:
        cleaned = [url.strip() for url in value if url and url.strip()]
        if not cleaned:
            raise ValueError("urls must contain at least one non-empty URL")
        return cleaned


class ProcessResponse(BaseModel):
    job_id: str


@router.post("/process", response_model=ProcessResponse)
async def start_process(body: ProcessRequest) -> ProcessResponse:
    language_codes = resolve_language_codes(body.language)
    job = job_store.create(body.urls, language_codes=language_codes)
    asyncio.create_task(run_job(job))
    return ProcessResponse(job_id=job.id)


@router.get("/process/{job_id}/events")
async def stream_process_events(job_id: str) -> StreamingResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream() -> AsyncIterator[str]:
        async for event in job.stream_events():
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
