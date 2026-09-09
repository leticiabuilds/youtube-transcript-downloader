"""HTTP routes for starting transcript processing jobs."""

from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.jobs import job_store, run_job

router = APIRouter(prefix="/api")


class ProcessRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1)

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
    job = job_store.create(body.urls)
    asyncio.create_task(run_job(job))
    return ProcessResponse(job_id=job.id)


@router.get("/process/{job_id}")
async def get_job(job_id: str) -> dict[str, str]:
    """Lightweight lookup used while SSE is not yet wired."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job.id, "status": job.status.value}
