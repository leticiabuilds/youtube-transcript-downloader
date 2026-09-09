"use client";

type DownloadZipButtonProps = {
  disabled: boolean;
  fileCount: number;
  onDownload: () => void;
};

export function DownloadZipButton({
  disabled,
  fileCount,
  onDownload,
}: DownloadZipButtonProps) {
  if (fileCount === 0) {
    return null;
  }

  return (
    <button
      type="button"
      onClick={onDownload}
      disabled={disabled}
      className="border border-ink bg-transparent px-4 py-2 text-sm text-ink transition-opacity hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {disabled
        ? "Preparing zip..."
        : `Download zip (${fileCount} file${fileCount === 1 ? "" : "s"})`}
    </button>
  );
}
