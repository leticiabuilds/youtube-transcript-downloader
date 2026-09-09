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
      className="border border-accent px-4 py-3 text-sm text-accent"
    >
      <p className="font-medium text-ink">YouTube rate limit reached</p>
      <p className="mt-1">{message}</p>
    </div>
  );
}
