"use client";

import { FormEvent, useState } from "react";

import { startProcess } from "@/lib/api";
import { parseYoutubeUrls } from "@/lib/urls";

type UrlInputFormProps = {
  isProcessing: boolean;
  onJobStarted: (payload: { jobId: string; urls: string[] }) => void;
};

export function UrlInputForm({ isProcessing, onJobStarted }: UrlInputFormProps) {
  const [rawUrls, setRawUrls] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const disabled = isProcessing || isSubmitting;
  const parsedCount = parseYoutubeUrls(rawUrls).length;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const urls = parseYoutubeUrls(rawUrls);
    if (urls.length === 0) {
      setError("Paste at least one YouTube URL (one per line).");
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await startProcess(urls);
      onJobStarted({ jobId: result.job_id, urls });
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Could not start processing.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <label htmlFor="youtube-urls" className="block text-sm text-ink">
          YouTube links
        </label>
        <textarea
          id="youtube-urls"
          name="youtube-urls"
          rows={8}
          value={rawUrls}
          onChange={(event) => setRawUrls(event.target.value)}
          disabled={disabled}
          placeholder={"https://www.youtube.com/watch?v=...\nhttps://youtu.be/..."}
          className="w-full resize-y border border-divider bg-canvas px-3 py-3 text-sm leading-relaxed text-ink outline-none placeholder:text-subtle focus:border-ink disabled:cursor-not-allowed disabled:opacity-60"
        />
        <p className="text-[13px] text-subtle">
          {parsedCount === 1
            ? "1 link ready"
            : `${parsedCount} links ready`}
          . One URL per line.
        </p>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-accent">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={disabled || parsedCount === 0}
        className="border border-ink bg-ink px-4 py-2 text-sm text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isProcessing || isSubmitting ? "Processing..." : "Start processing"}
      </button>
    </form>
  );
}
