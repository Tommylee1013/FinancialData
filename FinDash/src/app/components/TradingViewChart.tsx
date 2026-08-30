import React, { useEffect, useRef } from 'react';
import { CandlestickSeries, ColorType, LineSeries, createChart, type CandlestickData, type LineData, type Time } from 'lightweight-charts';

type Candle = { time?: string; date?: string; open: number; high: number; low: number; close: number };

export function TradingViewChart({ data, height = 320 }: { data: Candle[]; height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !data.length) return;
    const styles = getComputedStyle(document.documentElement);
    const foreground = styles.getPropertyValue('--foreground').trim() || '#111827';
    const border = styles.getPropertyValue('--border').trim() || '#E5E7EB';
    const background = styles.getPropertyValue('--card').trim() || '#FFFFFF';
    const chart = createChart(container, {
      width: container.clientWidth, height,
      layout: { background: { type: ColorType.Solid, color: background }, textColor: foreground, fontFamily: 'JetBrains Mono, monospace', fontSize: 10 },
      grid: { vertLines: { color: border, style: 1 }, horzLines: { color: border, style: 1 } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: border, scaleMargins: { top: 0.12, bottom: 0.12 } },
      timeScale: { borderColor: border, timeVisible: false, rightOffset: 3, barSpacing: 8, minBarSpacing: 3 },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale: { mouseWheel: true, pinch: true, axisPressedMouseMove: true },
      localization: { priceFormatter: price => price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#16A34A', downColor: '#DC2626', borderUpColor: '#16A34A', borderDownColor: '#DC2626', wickUpColor: '#16A34A', wickDownColor: '#DC2626',
      priceLineVisible: true, lastValueVisible: true,
    });
    const normalized = data.map((c, index) => ({
      time: (c.time ?? c.date ?? new Date(Date.now() - (data.length - index) * 86400000).toISOString().slice(0, 10)) as Time,
      open: c.open, high: c.high, low: c.low, close: c.close,
    })) as CandlestickData<Time>[];
    series.setData(normalized);
    const closes = normalized.map(candle => candle.close);
    const movingAverage = (period: number) => normalized.flatMap((candle, index) => {
      if (index < period - 1) return [];
      const window = closes.slice(index - period + 1, index + 1);
      return [{ time: candle.time, value: window.reduce((sum, value) => sum + value, 0) / period }];
    }) as LineData<Time>[];
    const bollinger = normalized.flatMap((candle, index) => {
      if (index < 19) return [];
      const window = closes.slice(index - 19, index + 1);
      const mean = window.reduce((sum, value) => sum + value, 0) / 20;
      const deviation = Math.sqrt(window.reduce((sum, value) => sum + Math.pow(value - mean, 2), 0) / 20);
      return [{ time: candle.time, middle: mean, upper: mean + deviation * 2, lower: mean - deviation * 2 }];
    });
    const ma5 = chart.addSeries(LineSeries, { color: '#F59E0B', lineWidth: 2, priceLineVisible: false, lastValueVisible: false, title: 'MA 5' });
    const bbMid = chart.addSeries(LineSeries, { color: '#8B5CF6', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, title: 'BB 20' });
    const bbUpper = chart.addSeries(LineSeries, { color: 'rgba(139,92,246,0.65)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    const bbLower = chart.addSeries(LineSeries, { color: 'rgba(139,92,246,0.65)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    ma5.setData(movingAverage(5));
    bbMid.setData(bollinger.map(point => ({ time: point.time, value: point.middle })) as LineData<Time>[]);
    bbUpper.setData(bollinger.map(point => ({ time: point.time, value: point.upper })) as LineData<Time>[]);
    bbLower.setData(bollinger.map(point => ({ time: point.time, value: point.lower })) as LineData<Time>[]);
    chart.timeScale().fitContent();
    const observer = new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth }));
    observer.observe(container);
    return () => { observer.disconnect(); chart.remove(); };
  }, [data, height]);

  return <div className="relative w-full"><div className="absolute z-10 top-2 left-3 flex gap-3 text-[10px] font-mono pointer-events-none"><span className="flex items-center gap-1 text-muted-foreground"><i className="w-3 h-0.5 bg-yellow-500"/>MA 5</span><span className="flex items-center gap-1 text-muted-foreground"><i className="w-3 h-0.5 bg-violet-500"/>BB 20 · 2σ</span></div><div ref={containerRef} className="w-full" style={{ height }} /></div>;
}
