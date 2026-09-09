export type VideoStatus =
  | "aguardando"
  | "processando"
  | "concluido"
  | "falhou";

export type VideoItemState = {
  url: string;
  status: VideoStatus;
  filename?: string;
  content?: string;
  error?: string;
};

export type StatusUpdateEvent = {
  type: "status_update";
  url: string;
  status: VideoStatus;
  filename?: string;
  content?: string;
  error?: string;
};

export type RateLimitedEvent = {
  type: "rate_limited";
  message: string;
};

export type DoneEvent = {
  type: "done";
};

export type ProcessEvent = StatusUpdateEvent | RateLimitedEvent | DoneEvent;

export function isProcessEvent(value: unknown): value is ProcessEvent {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (record.type === "done") {
    return true;
  }
  if (record.type === "rate_limited" && typeof record.message === "string") {
    return true;
  }
  if (
    record.type === "status_update" &&
    typeof record.url === "string" &&
    typeof record.status === "string"
  ) {
    return true;
  }
  return false;
}
