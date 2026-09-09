"use client";

import { useEffect, useState } from "react";

import { UrlInputForm } from "@/components/UrlInputForm";
import { VideoStatusList } from "@/components/VideoStatusList";
import { getProcessEventsUrl } from "@/lib/api";
import {
  isProcessEvent,
  type VideoItemState,
} from "@/lib/processEvents";

type ActiveJob = {
  jobId: string;
  urls: string[];
};

function createInitialItems(urls: string[]): VideoItemState[] {
  return urls.map((url) => ({
    url,
    status: "aguardando",
  }));
}

export function ProcessWorkspace() {
  const [activeJob, setActiveJob] = useState<ActiveJob | null>(null);
  const [items, setItems] = useState<VideoItemState[]>([]);
  const [streamError, setStreamError] = useState<string | null>(null);
  const isProcessing = activeJob !== null;

  useEffect(() => {
    if (!activeJob) {
      return;
    }

    const source = new EventSource(getProcessEventsUrl(activeJob.jobId));

    source.onmessage = (message) => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(message.data) as unknown;
      } catch {
        setStreamError("Received an invalid progress event.");
        source.close();
        setActiveJob(null);
        return;
      }

      if (!isProcessEvent(parsed)) {
        return;
      }

      if (parsed.type === "status_update") {
        setItems((current) => {
          const next = [...current];
          const index = next.findIndex((item) => item.url === parsed.url);
          const updated: VideoItemState = {
            url: parsed.url,
            status: parsed.status,
            filename: parsed.filename,
            content: parsed.content,
            error: parsed.error,
          };
          if (index === -1) {
            next.push(updated);
          } else {
            next[index] = { ...next[index], ...updated };
          }
          return next;
        });
        return;
      }

      if (parsed.type === "rate_limited") {
        return;
      }

      if (parsed.type === "done") {
        source.close();
        setActiveJob(null);
      }
    };

    source.onerror = () => {
      setStreamError("Lost connection to the progress stream.");
      source.close();
      setActiveJob(null);
    };

    return () => {
      source.close();
    };
  }, [activeJob]);

  return (
    <div className="mt-12 space-y-10">
      <UrlInputForm
        isProcessing={isProcessing}
        onJobStarted={({ jobId, urls }) => {
          setStreamError(null);
          setItems(createInitialItems(urls));
          setActiveJob({ jobId, urls });
        }}
      />

      {streamError ? (
        <p role="alert" className="text-sm text-accent">
          {streamError}
        </p>
      ) : null}

      <VideoStatusList items={items} />
    </div>
  );
}
