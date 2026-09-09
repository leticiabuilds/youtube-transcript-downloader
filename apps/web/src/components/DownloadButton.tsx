"use client";

type DownloadButtonProps = {
  disabled: boolean;
  fileCount: number;
  onDownload: () => void;
};

export function DownloadButton({
  disabled,
  fileCount,
  onDownload,
}: DownloadButtonProps) {
  if (fileCount === 0) {
    return null;
  }

  const label =
    fileCount === 1
      ? disabled
        ? "Preparing file..."
        : "Download txt"
      : disabled
        ? "Preparing zip..."
        : `Download zip (${fileCount} files)`;

  return (
    <button
      type="button"
      onClick={onDownload}
      disabled={disabled}
      className="rounded-full border border-ink bg-transparent px-5 py-2.5 text-sm text-ink transition-opacity hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {label}
    </button>
  );
}
