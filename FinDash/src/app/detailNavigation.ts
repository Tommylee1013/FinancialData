export type DetailKind = 'benchmark' | 'market' | 'volatility' | 'macro' | 'commodity' | 'freight' | 'industry' | 'fixed-income' | 'sector' | 'sentiment';

export function openDetail(kind: DetailKind, id: string) {
  window.location.hash = `detail/${kind}/${encodeURIComponent(id)}`;
}

export function readDetailRoute() {
  const match = window.location.hash.match(/^#detail\/([^/]+)\/(.+)$/);
  return match ? { kind: match[1] as DetailKind, id: decodeURIComponent(match[2]) } : null;
}
