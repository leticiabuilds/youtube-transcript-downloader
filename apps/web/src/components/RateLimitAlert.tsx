"use client";

type RateLimitAlertProps = {
  message: string | null;
};

export function RateLimitAlert({ message }: RateLimitAlertProps) {
  if (!message) {
    return null;
  }

  return (
    <div
      role="alert"
      className="radius border border-divider bg-canvas px-3 py-3 text-sm text-accent shadow-[0_6px_20px_-8px_rgba(0,0,0,0.12)]"
    >
      <p className="font-medium text-ink">YouTube rate limit reached</p>
      <p className="mt-1">{message}</p>
    </div>
  );
}
