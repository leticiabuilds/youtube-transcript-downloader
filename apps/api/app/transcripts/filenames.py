"""Build safe .txt filenames from YouTube video ids.

MVP decision: use the video id as the filename stem (not the video title).
Still sanitize so only alphanumeric characters, underscores, and hyphens remain.
"""

from __future__ import annotations

import re

_SAFE_STEM_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")


def transcript_filename(video_id: str) -> str:
    """Return `{sanitized-video-id}.txt`."""
    stem = _SAFE_STEM_PATTERN.sub("", video_id.strip())
    if not stem:
        raise ValueError("video_id produced an empty filename stem")
    return f"{stem}.txt"
