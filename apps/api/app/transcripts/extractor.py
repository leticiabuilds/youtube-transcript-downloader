"""Fetch plain-text YouTube transcripts via youtube-transcript-api."""

from __future__ import annotations

from dataclasses import dataclass

from youtube_transcript_api import (
    AgeRestricted,
    CouldNotRetrieveTranscript,
    InvalidVideoId,
    IpBlocked,
    NoTranscriptFound,
    PoTokenRequired,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeRequestFailed,
    YouTubeTranscriptApi,
)

from app.transcripts.exceptions import DefinitiveTranscriptError, RateLimitError
from app.transcripts.filenames import transcript_filename
from app.transcripts.urls import extract_video_id


@dataclass(frozen=True)
class TranscriptResult:
    url: str
    video_id: str
    filename: str
    content: str
    language_code: str


def fetch_transcript(url: str) -> TranscriptResult:
    """Extract the first available transcript for a YouTube URL as plain text.

    Uses whichever caption track YouTube exposes first (manual preferred by the
    library list order, then generated). Does not require a language picker.
    """
    video_id = extract_video_id(url)
    filename = transcript_filename(video_id)

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            transcript = next(iter(transcript_list))
        except StopIteration as exc:
            raise DefinitiveTranscriptError(
                "No transcript available for this video"
            ) from exc

        fetched = transcript.fetch()
    except RateLimitError:
        raise
    except DefinitiveTranscriptError:
        raise
    except (IpBlocked, RequestBlocked, PoTokenRequired) as exc:
        raise RateLimitError(
            "Rate limit or IP block from YouTube. Try again later."
        ) from exc
    except YouTubeRequestFailed as exc:
        if _looks_like_http_429(exc):
            raise RateLimitError(
                "Rate limit or IP block from YouTube. Try again later."
            ) from exc
        raise DefinitiveTranscriptError(
            f"YouTube request failed: {exc.cause}"
        ) from exc
    except InvalidVideoId as exc:
        raise DefinitiveTranscriptError("Invalid YouTube video id") from exc
    except VideoUnavailable as exc:
        raise DefinitiveTranscriptError("Video is unavailable") from exc
    except VideoUnplayable as exc:
        raise DefinitiveTranscriptError("Video is unplayable") from exc
    except AgeRestricted as exc:
        raise DefinitiveTranscriptError("Video is age-restricted") from exc
    except TranscriptsDisabled as exc:
        raise DefinitiveTranscriptError("Transcripts are disabled for this video") from exc
    except NoTranscriptFound as exc:
        raise DefinitiveTranscriptError("No transcript available for this video") from exc
    except CouldNotRetrieveTranscript as exc:
        raise DefinitiveTranscriptError(
            f"Could not retrieve transcript: {exc.cause}"
        ) from exc

    content = _to_plain_text(fetched)
    if not content.strip():
        raise DefinitiveTranscriptError("Transcript was empty")

    return TranscriptResult(
        url=url.strip(),
        video_id=video_id,
        filename=filename,
        content=content,
        language_code=fetched.language_code,
    )


def _to_plain_text(fetched: object) -> str:
    snippets = getattr(fetched, "snippets", fetched)
    parts: list[str] = []
    for snippet in snippets:
        text = getattr(snippet, "text", None)
        if text is None and isinstance(snippet, dict):
            text = snippet.get("text", "")
        if not text:
            continue
        parts.append(str(text).replace("\n", " ").strip())
    return " ".join(part for part in parts if part)


def _looks_like_http_429(exc: YouTubeRequestFailed) -> bool:
    reason = getattr(exc, "reason", "") or str(exc)
    return "429" in reason
