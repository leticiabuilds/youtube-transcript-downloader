"""Process-memory job store. Jobs are lost when the API process exits."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Sequence, Tuple

from app.jobs.models import Job


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}

    def create(
        self,
        urls: List[str],
        language_codes: Sequence[str] = ("en",),
    ) -> Job:
        job_id = uuid.uuid4().hex
        codes: Tuple[str, ...] = tuple(language_codes) if language_codes else ("en",)
        job = Job(id=job_id, urls=urls, language_codes=codes)
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)


job_store = JobStore()
