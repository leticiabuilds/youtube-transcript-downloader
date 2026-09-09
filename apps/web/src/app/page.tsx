import { ProcessWorkspace } from "@/components/ProcessWorkspace";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-6 py-24 sm:px-8 sm:py-32">
      <header className="space-y-4">
        <h1 className="font-serif text-[40px] font-normal leading-snug text-ink">
          YouTube Transcript Downloader
        </h1>
        <p className="max-w-md text-sm leading-relaxed text-body">
          Paste YouTube links, watch each video process locally, and download a
          zip of successful transcripts. No deploy. No database.
        </p>
      </header>

      <ProcessWorkspace />
    </main>
  );
}
