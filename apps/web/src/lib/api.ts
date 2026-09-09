const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

export function getProcessEventsUrl(jobId: string): string {
  return `${getApiBaseUrl()}/api/process/${encodeURIComponent(jobId)}/events`;
}

export type StartProcessResponse = {
  job_id: string;
};

export async function startProcess(urls: string[]): Promise<StartProcessResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ urls }),
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      // Keep the status-based message when the body is not JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as StartProcessResponse;
}
