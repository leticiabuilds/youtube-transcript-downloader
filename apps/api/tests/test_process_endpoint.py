"""Tests for POST /api/process job creation."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.jobs.store import job_store


class ProcessEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        job_store._jobs.clear()
        self.client = TestClient(app)

    def test_rejects_empty_urls(self) -> None:
        response = self.client.post("/api/process", json={"urls": []})
        self.assertEqual(response.status_code, 422)

    def test_rejects_whitespace_only_urls(self) -> None:
        response = self.client.post("/api/process", json={"urls": ["  ", ""]})
        self.assertEqual(response.status_code, 422)

    @patch("app.routes.process.run_job", new_callable=AsyncMock)
    def test_creates_job_and_returns_id(self, mock_run_job: AsyncMock) -> None:
        response = self.client.post(
            "/api/process",
            json={
                "urls": [
                    "https://www.youtube.com/watch?v=aaaaaaaaaaa",
                    " https://youtu.be/bbbbbbbbbbb ",
                ]
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("job_id", payload)
        job = job_store.get(payload["job_id"])
        self.assertIsNotNone(job)
        assert job is not None
        self.assertEqual(
            job.urls,
            [
                "https://www.youtube.com/watch?v=aaaaaaaaaaa",
                "https://youtu.be/bbbbbbbbbbb",
            ],
        )
        mock_run_job.assert_awaited()

    def test_cors_allows_local_next_origin(self) -> None:
        response = self.client.options(
            "/api/process",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:3000",
        )


if __name__ == "__main__":
    unittest.main()
