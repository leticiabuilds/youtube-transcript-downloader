export function parseYoutubeUrls(raw: string): string[] {
  const lines = raw.split(/\r?\n/);
  const urls: string[] = [];
  const seen = new Set<string>();

  for (const line of lines) {
    const url = line.trim();
    if (!url) {
      continue;
    }
    if (seen.has(url)) {
      continue;
    }
    seen.add(url);
    urls.push(url);
  }

  return urls;
}
