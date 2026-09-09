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
      className="radius border-0 bg-[color-mix(in_srgb,var(--color-divider)_65%,var(--color-bg))] px-3.5 py-2.5 text-[13px] font-semibold leading-tight text-accent transition-colors hover:bg-[color-mix(in_srgb,var(--color-accent)_10%,var(--color-bg))] focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40"
    >
      {label}
    </button>
  );
}
