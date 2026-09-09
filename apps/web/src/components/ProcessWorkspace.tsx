"use client";

import { useEffect, useRef, useState } from "react";

import { DownloadButton } from "@/components/DownloadButton";
import { RateLimitAlert } from "@/components/RateLimitAlert";
import { UrlInputForm } from "@/components/UrlInputForm";
import { VideoStatusList } from "@/components/VideoStatusList";
import { getProcessEventsUrl } from "@/lib/api";
import {
  downloadTranscripts,
  type TranscriptFile,
} from "@/lib/downloadZip";
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

function collectSuccessfulFiles(items: VideoItemState[]): TranscriptFile[] {
  const files: TranscriptFile[] = [];
  for (const item of items) {
    if (
      item.status === "concluido" &&
      item.filename &&
      typeof item.content === "string"
    ) {
      files.push({
        filename: item.filename,
        content: item.content,
      });
    }
  }
  return files;
}

export function ProcessWorkspace() {
  const [activeJob, setActiveJob] = useState<ActiveJob | null>(null);
  const [items, setItems] = useState<VideoItemState[]>([]);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [rateLimitMessage, setRateLimitMessage] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [clearSignal, setClearSignal] = useState(0);
  const successfulFilesRef = useRef<TranscriptFile[]>([]);
  const isProcessing = activeJob !== null;
  const successfulFiles = collectSuccessfulFiles(items);

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

        if (
          parsed.status === "concluido" &&
          parsed.filename &&
          typeof parsed.content === "string"
        ) {
          const exists = successfulFilesRef.current.some(
            (file) => file.filename === parsed.filename,
          );
          if (!exists) {
            successfulFilesRef.current.push({
              filename: parsed.filename,
              content: parsed.content,
            });
          }
        }
        return;
      }

      if (parsed.type === "rate_limited") {
        setRateLimitMessage(parsed.message);
        return;
      }

      if (parsed.type === "done") {
        source.close();
        setActiveJob(null);
        setClearSignal((current) => current + 1);
        void finalizeDownload(successfulFilesRef.current);
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

  async function finalizeDownload(files: TranscriptFile[]) {
    if (files.length === 0) {
      return;
    }
    setDownloadError(null);
    setIsDownloading(true);
    try {
      await downloadTranscripts(files);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Could not prepare the download.";
      setDownloadError(message);
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="mt-12 space-y-10">
      <UrlInputForm
        isProcessing={isProcessing}
        clearSignal={clearSignal}
        onJobStarted={({ jobId, urls }) => {
          setStreamError(null);
          setRateLimitMessage(null);
          setDownloadError(null);
          successfulFilesRef.current = [];
          setItems(createInitialItems(urls));
          setActiveJob({ jobId, urls });
        }}
      />

      <RateLimitAlert message={rateLimitMessage} />

      {streamError ? (
        <p role="alert" className="text-sm text-accent">
          {streamError}
        </p>
      ) : null}

      {downloadError ? (
        <p role="alert" className="text-sm text-accent">
          {downloadError}
        </p>
      ) : null}

      <VideoStatusList items={items} />

      <DownloadButton
        disabled={isProcessing || isDownloading}
        fileCount={successfulFiles.length}
        onDownload={() => {
          void finalizeDownload(successfulFiles);
        }}
      />
    </div>
  );
}
