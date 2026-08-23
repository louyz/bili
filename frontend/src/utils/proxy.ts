export function proxyImage(url: string | undefined | null): string {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return `/api/proxy/image?url=${encodeURIComponent(url)}`;
  }
  return url;
}