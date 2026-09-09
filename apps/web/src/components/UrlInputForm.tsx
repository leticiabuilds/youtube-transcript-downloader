"use client";

import { FormEvent, useEffect, useState } from "react";

import { startProcess, type TranscriptLanguage } from "@/lib/api";
import { parseYoutubeUrls } from "@/lib/urls";

type UrlInputFormProps = {
  isProcessing: boolean;
  clearSignal: number;
  onJobStarted: (payload: {
    jobId: string;
    urls: string[];
    language: TranscriptLanguage;
  }) => void;
};

export function UrlInputForm({
  isProcessing,
  clearSignal,
  onJobStarted,
}: UrlInputFormProps) {
  const [rawUrls, setRawUrls] = useState("");
  const [language, setLanguage] = useState<TranscriptLanguage>("en");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const disabled = isProcessing || isSubmitting;
  const parsedCount = parseYoutubeUrls(rawUrls).length;

  useEffect(() => {
    if (clearSignal === 0) {
      return;
    }
    setRawUrls("");
    setError(null);
  }, [clearSignal]);

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
      const result = await startProcess(urls, language);
      onJobStarted({ jobId: result.job_id, urls, language });
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
          className="w-full resize-y rounded-[14px] border border-divider bg-canvas px-4 py-3 text-sm leading-relaxed text-ink outline-none placeholder:text-subtle focus:border-ink disabled:cursor-not-allowed disabled:opacity-60"
        />
        <p className="text-[13px] text-subtle">
          {parsedCount === 1
            ? "1 link ready"
            : `${parsedCount} links ready`}
          . One URL per line.
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="transcript-language" className="block text-sm text-ink">
          Transcript language
        </label>
        <select
          id="transcript-language"
          name="transcript-language"
          value={language}
          onChange={(event) =>
            setLanguage(event.target.value as TranscriptLanguage)
          }
          disabled={disabled}
          className="w-full rounded-[14px] border border-divider bg-canvas px-4 py-3 text-sm text-ink outline-none focus:border-ink disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          <option value="en">English</option>
          <option value="pt">Portuguese</option>
        </select>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-accent">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={disabled || parsedCount === 0}
        className="rounded-full border border-ink bg-ink px-5 py-2.5 text-sm text-canvas transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isProcessing || isSubmitting ? "Processing..." : "Start processing"}
      </button>
    </form>
  );
}
