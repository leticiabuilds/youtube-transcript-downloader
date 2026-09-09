from fastapi import FastAPI

app = FastAPI(
    title="YouTube Transcript Downloader API",
    description="Local API that fetches YouTube transcripts and streams processing progress.",
    version="0.1.0",
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
