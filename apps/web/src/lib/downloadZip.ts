import JSZip from "jszip";

export type TranscriptFile = {
  filename: string;
  content: string;
};

export async function buildTranscriptZip(
  files: TranscriptFile[],
): Promise<Blob> {
  const zip = new JSZip();

  for (const file of files) {
    zip.file(file.filename, file.content);
  }

  return zip.generateAsync({ type: "blob" });
}

export function downloadBlob(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export async function downloadTranscripts(
  files: TranscriptFile[],
  zipName = "youtube-transcripts.zip",
): Promise<void> {
  if (files.length === 0) {
    return;
  }

  if (files.length === 1) {
    const file = files[0];
    const blob = new Blob([file.content], {
      type: "text/plain;charset=utf-8",
    });
    downloadBlob(blob, file.filename);
    return;
  }

  const blob = await buildTranscriptZip(files);
  downloadBlob(blob, zipName);
}
