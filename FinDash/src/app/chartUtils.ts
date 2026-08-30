export function paddedDomain(values: Array<number | null | undefined>, minimumPadding = 0.01): [number, number] {
  const finite = values.filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
  if (!finite.length) return [0, 1];
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const span = max - min;
  const pad = Math.max(span * 0.14, Math.abs(max || 1) * 0.015, minimumPadding);
  return [min - pad, max + pad];
}
