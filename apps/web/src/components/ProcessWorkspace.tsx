"use client";

import { useState } from "react";

import { UrlInputForm } from "@/components/UrlInputForm";

type ActiveJob = {
  jobId: string;
  urls: string[];
};

export function ProcessWorkspace() {
  const [activeJob, setActiveJob] = useState<ActiveJob | null>(null);
  const isProcessing = activeJob !== null;

  return (
    <section className="mt-12">
      <UrlInputForm
        isProcessing={isProcessing}
        onJobStarted={({ jobId, urls }) => {
          setActiveJob({ jobId, urls });
        }}
      />
    </section>
  );
}
