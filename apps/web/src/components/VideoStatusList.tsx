"use client";

import type { VideoItemState, VideoStatus } from "@/lib/processEvents";

const STATUS_LABELS: Record<VideoStatus, string> = {
  aguardando: "Waiting",
  processando: "Processing",
  concluido: "Completed",
  falhou: "Failed",
};

type VideoStatusListProps = {
  items: VideoItemState[];
};

export function VideoStatusList({ items }: VideoStatusListProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="space-y-3" aria-live="polite">
      <h2 className="font-serif text-[24px] font-normal leading-snug text-ink">
        Progress
      </h2>
      <ul className="border-y border-divider divide-y divide-divider">
        {items.map((item) => {
          const isActive = item.status === "processando";
          return (
            <li
              key={item.url}
              className={`py-4 pr-2 transition-colors duration-300 ease-in-out ${
                isActive ? "text-accent" : ""
              }`}
            >
              <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4">
                <p
                  className={`break-all text-sm ${
                    isActive ? "text-ink" : "text-body"
                  }`}
                >
                  {item.url}
                </p>
                <p
                  className={`shrink-0 text-[13px] ${
                    item.status === "falhou"
                      ? "text-accent"
                      : item.status === "concluido"
                        ? "text-ink"
                        : isActive
                          ? "text-accent"
                          : "text-subtle"
                  }`}
                >
                  {STATUS_LABELS[item.status]}
                </p>
              </div>
              {item.status === "falhou" && item.error ? (
                <p className="mt-1 text-[13px] text-accent">{item.error}</p>
              ) : null}
              {item.status === "concluido" && item.filename ? (
                <p className="mt-1 text-[13px] text-subtle">{item.filename}</p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
