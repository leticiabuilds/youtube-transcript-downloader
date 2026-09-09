from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import process_router

app = FastAPI(
    title="YouTube Transcript Downloader API",
    description="Local API that fetches YouTube transcripts and streams processing progress.",
    version="0.1.0",
)

# Local Next.js app only. This project is not intended for deployed multi-origin use.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
