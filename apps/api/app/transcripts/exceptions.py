"""Domain exceptions for transcript extraction.

Definitive errors fail a single video and let the queue continue.
Rate-limit errors signal that remaining work must be cancelled (wired in later tasks).
"""


class TranscriptError(Exception):
    """Base error for transcript extraction."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DefinitiveTranscriptError(TranscriptError):
    """Video-specific failure that should not stop the rest of the queue."""


class RateLimitError(TranscriptError):
    """YouTube blocked or rate-limited the client. Remaining queue items must be cancelled."""
