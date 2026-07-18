import React, { useMemo } from "react";

interface OHLC {
  t: number;
  open: number;
  high: number;
  low: number;
  close: number;
  date?: string;
}

interface CandlestickChartProps {
  data: OHLC[];
  width?: number;
  height?: number;
  showAxes?: boolean;
}

export function CandlestickChart({ data, width = 320, height = 160, showAxes = false }: CandlestickChartProps) {
  const { minVal, maxVal, candleWidth, gap } = useMemo(() => {
    const allValues = data.flatMap(d => [d.high, d.low]);
    const minVal = Math.min(...allValues);
    const maxVal = Math.max(...allValues);
    const totalWidth = width - (showAxes ? 40 : 8);
    const gap = Math.max(1, Math.floor(totalWidth / data.length * 0.2));
    const candleWidth = Math.max(2, Math.floor(totalWidth / data.length) - gap);
    return { minVal, maxVal, candleWidth, gap };
  }, [data, width, showAxes]);

  const scaleY = (val: number) => {
    const pad = showAxes ? 10 : 4;
    const range = maxVal - minVal || 1;
    return height - pad - ((val - minVal) / range) * (height - pad * 2);
  };

  const xOffset = showAxes ? 38 : 4;

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {showAxes && (
        <>
          {[0, 0.25, 0.5, 0.75, 1].map(t => {
            const val = minVal + t * (maxVal - minVal);
            const y = scaleY(val);
            return (
              <g key={t}>
                <line x1={xOffset} y1={y} x2={width} y2={y} stroke="currentColor" strokeOpacity={0.08} strokeWidth={1} />
                <text x={xOffset - 4} y={y + 3} textAnchor="end" fontSize={9} fill="currentColor" fillOpacity={0.45} fontFamily="JetBrains Mono, monospace">
                  {val.toFixed(0)}
                </text>
              </g>
            );
          })}
        </>
      )}
      {data.map((d, i) => {
        const x = xOffset + i * (candleWidth + gap) + candleWidth / 2;
        const isUp = d.close >= d.open;
        const color = isUp ? '#16A34A' : '#DC2626';
        const bodyTop = scaleY(Math.max(d.open, d.close));
        const bodyBottom = scaleY(Math.min(d.open, d.close));
        const bodyHeight = Math.max(1, bodyBottom - bodyTop);

        return (
          <g key={i}>
            <line
              x1={x}
              y1={scaleY(d.high)}
              x2={x}
              y2={scaleY(d.low)}
              stroke={color}
              strokeWidth={1}
            />
            <rect
              x={x - candleWidth / 2}
              y={bodyTop}
              width={candleWidth}
              height={bodyHeight}
              fill={isUp ? color : color}
              fillOpacity={isUp ? 0.85 : 0.85}
              stroke={color}
              strokeWidth={0.5}
            />
          </g>
        );
      })}
    </svg>
  );
}

interface MiniLineProps {
  data: { t: number; v: number }[];
  width?: number;
  height?: number;
  color?: string;
  fill?: boolean;
}

export function MiniLineChart({ data, width = 100, height = 36, color = '#1A56DB', fill = true }: MiniLineProps) {
  if (!data || data.length < 2) return null;
  const vals = data.map(d => d.v);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const padY = 2;
  const scaleX = (i: number) => (i / (data.length - 1)) * (width - 2) + 1;
  const scaleY = (v: number) => height - padY - ((v - min) / range) * (height - padY * 2);

  const linePts = data.map((d, i) => `${scaleX(i)},${scaleY(d.v)}`).join(' ');
  const fillPts = `${scaleX(0)},${height} ${linePts} ${scaleX(data.length - 1)},${height}`;

  return (
    <svg width={width} height={height} style={{ display: 'block', overflow: 'visible' }}>
      {fill && (
        <polygon points={fillPts} fill={color} fillOpacity={0.12} />
      )}
      <polyline points={linePts} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
    </svg>
  );
}
