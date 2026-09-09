# YouTube Transcript Downloader

Local tool that takes a list of YouTube links, fetches each available transcript, and downloads the results as `.txt` files (one file for a single success, a zip for multiple successes).

It exists to remove the manual copy and paste loop when you need transcripts from several videos at once.

## Local only

This project is meant to run on your machine only.

- No deploy target
- No database
- No persistence between sessions

Restarting the API clears in-memory jobs.

## Stack

| Layer | Technology |
| --- | --- |
| Monorepo | Turborepo (npm workspaces) |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, uvicorn |
| Transcripts | `youtube-transcript-api` |
| Progress | HTTP POST + Server-Sent Events |
| Download | JSZip in the browser, `URL.createObjectURL` |

## Prerequisites

- Node.js 20 or newer
- npm 10 or newer
- Python 3.9 or newer

## Setup

From the repository root:

```bash
npm install
npm run local-dev
```

What `npm run local-dev` does:

1. Creates `apps/api/.venv` if it does not exist
2. Installs Python dependencies from `apps/api/requirements.txt`
3. Starts the API on `http://127.0.0.1:8000`
4. Starts the web app on `http://localhost:3000`

Useful related commands:

```bash
npm run setup:api   # only prepare the Python venv and dependencies
npm run dev         # start both apps if the API venv is already ready
```

Optional frontend env file:

```bash
cp apps/web/.env.example apps/web/.env.local
```

Default API base URL is `http://127.0.0.1:8000`.

Manual API setup, if you prefer not to use the helper script:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../..
npm run dev
```

On Windows, activate the venv with:

```bash
apps\api\.venv\Scripts\activate
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response: `{"status":"ok"}`.

## How to use

1. Open `http://localhost:3000`
2. Paste one YouTube URL per line
3. Choose transcript language (`English` by default, or `Portuguese`)
4. Click **Start processing**
5. Watch live status for each URL
6. When the job finishes:
   - one successful transcript downloads as a `.txt` file
   - two or more successful transcripts download as `youtube-transcripts.zip`
7. Failed videos are listed with an error reason and are not included in the download
8. If YouTube rate-limits the client, remaining queue items are cancelled and a global alert appears. Successful files collected before that point are still downloaded.

File names use the YouTube video id, for example `dQw4w9WgXcQ.txt`.

## Known limitations

- Transcript language is selected up front (`en` or `pt` / `pt-BR`). If that language is missing for a video, that item fails.
- There is no retry or exponential backoff on rate limit. The remaining queue is cancelled.
- Jobs live only in API process memory.
- Docker Compose is not part of the current setup.
- Video titles are not used for file names in this version.

## Contributing

This is an open source project.

1. Open an issue or pull request with a clear description of the change
2. Keep changes focused
3. Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages, for example:
   - `feat: ...`
   - `fix: ...`
   - `docs: ...`
   - `chore: ...`
4. Do not add deploy or persistence features unless that is the explicit goal of the change

## License

MIT. See [LICENSE](./LICENSE).
