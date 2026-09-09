"""Parse YouTube URLs into video IDs."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from app.transcripts.exceptions import DefinitiveTranscriptError

# Standard YouTube video ids are 11 chars from [A-Za-z0-9_-].
_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(url: str) -> str:
    """Return the video id from a YouTube URL or raise DefinitiveTranscriptError."""
    raw = url.strip()
    if not raw:
        raise DefinitiveTranscriptError("Empty YouTube URL")

    if _VIDEO_ID_PATTERN.fullmatch(raw):
        return raw

    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()

    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.lstrip("/").split("/")[0]
        return _validated_video_id(candidate)

    if host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        if parsed.path == "/watch":
            values = parse_qs(parsed.query).get("v", [])
            if values:
                return _validated_video_id(values[0])

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts", "live", "v"}:
            return _validated_video_id(path_parts[1])

    raise DefinitiveTranscriptError(f"Invalid YouTube URL: {raw}")


def _validated_video_id(candidate: str) -> str:
    if not _VIDEO_ID_PATTERN.fullmatch(candidate):
        raise DefinitiveTranscriptError(f"Invalid YouTube video id: {candidate}")
    return candidate
