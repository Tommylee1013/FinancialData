import React, { useMemo, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { paddedDomain } from '../chartUtils';
import { TradingViewChart } from './TradingViewChart';

export type ChartInterval = 'D' | 'W' | 'M' | 'Q' | 'Y';
export type ChartMode = 'line' | 'candle';

type SourcePoint = {
  date?: string; period?: string; time?: string; t?: string | number;
  value?: number; v?: number; open?: number; high?: number; low?: number; close?: number;
};

type CandlePoint = { time: string; date: string; open: number; high: number; low: number; close: number };

const fmt = (value: number, digits: number) => value.toLocaleString('en-US', { maximumFractionDigits: digits });

function pointDate(point: SourcePoint, index: number) {
  const candidate = point.date ?? point.period ?? point.time ?? (typeof point.t === 'string' ? point.t : undefined);
  const parsed = candidate ? new Date(candidate) : new Date(NaN);
  if (!Number.isNaN(parsed.getTime())) return parsed;
  const fallback = new Date(); fallback.setDate(fallback.getDate() - index);
  return fallback;
}

function bucketDate(date: Date, interval: ChartInterval) {
  const value = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  if (interval === 'W') {
    const day = value.getUTCDay() || 7;
    value.setUTCDate(value.getUTCDate() - day + 1);
  } else if (interval === 'M') {
    value.setUTCDate(1);
  } else if (interval === 'Q') {
    value.setUTCMonth(Math.floor(value.getUTCMonth() / 3) * 3, 1);
  } else if (interval === 'Y') {
    value.setUTCMonth(0, 1);
  }
  return value.toISOString().slice(0, 10);
}

export function aggregateOHLC(data: SourcePoint[], interval: ChartInterval): CandlePoint[] {
  const sorted = data.map((point, index) => ({ point, date: pointDate(point, data.length - 1 - index) }))
    .filter(row => !Number.isNaN(row.date.getTime()))
    .sort((a, b) => a.date.getTime() - b.date.getTime());
  const groups = new Map<string, CandlePoint>();
  for (const { point, date } of sorted) {
    const close = Number(point.close ?? point.value ?? point.v);
    if (!Number.isFinite(close)) continue;
    const open = Number.isFinite(Number(point.open)) ? Number(point.open) : close;
    const high = Number.isFinite(Number(point.high)) ? Number(point.high) : Math.max(open, close);
    const low = Number.isFinite(Number(point.low)) ? Number(point.low) : Math.min(open, close);
    const key = bucketDate(date, interval);
    const existing = groups.get(key);
    if (!existing) groups.set(key, { time: key, date: key, open, high, low, close });
    else {
      existing.high = Math.max(existing.high, high, open, close);
      existing.low = Math.min(existing.low, low, open, close);
      existing.close = close;
    }
  }
  return Array.from(groups.values());
}

export function TimeSeriesChart({ data, height = 330, color = 'var(--primary)', digits = 2, initialMode = 'line', initialMonths = 1200 }: {
  data: SourcePoint[]; height?: number; color?: string; digits?: number; initialMode?: ChartMode; initialMonths?: number;
}) {
  const [mode, setMode] = useState<ChartMode>(initialMode);
  const [interval, setInterval] = useState<ChartInterval>('D');
  const candles = useMemo(() => aggregateOHLC(data, interval), [data, interval]);
  const lineData = candles.map(point => ({ period: point.date, value: point.close }));
  const domain = paddedDomain(lineData.map(point => point.value));
  const latest = candles.at(-1);
  const button = (active: boolean) => `px-2 py-1 rounded border text-[10px] font-semibold ${active ? 'bg-primary text-primary-foreground border-primary' : 'border-border text-muted-foreground hover:text-foreground'}`;

  return <div>
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-1">
        <button onClick={() => setMode('line')} className={button(mode === 'line')}>Line</button>
        <button onClick={() => setMode('candle')} className={button(mode === 'candle')}>Candlestick</button>
      </div>
      <div className="flex items-center gap-1">
        {([['D','Daily'],['W','Weekly'],['M','Monthly'],['Q','Quarterly'],['Y','Yearly']] as const).map(([key, label]) => <button key={key} onClick={() => setInterval(key)} className={button(interval === key)}>{label}</button>)}
      </div>
    </div>
    {latest && <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-muted-foreground">
      <span>{latest.date}</span><span>O <b className="text-foreground">{fmt(latest.open, digits)}</b></span><span>H <b className="text-up">{fmt(latest.high, digits)}</b></span><span>L <b className="text-down">{fmt(latest.low, digits)}</b></span><span>C <b className="text-foreground">{fmt(latest.close, digits)}</b></span><span>{candles.length.toLocaleString()} bars</span>
    </div>}
    {mode === 'candle' ? <TradingViewChart data={candles} height={height} initialMonths={initialMonths}/> :
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={lineData} margin={{ top: 10, right: 10, left: 5, bottom: 0 }}>
          <defs><linearGradient id="timeSeriesFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={color} stopOpacity={0.24}/><stop offset="95%" stopColor={color} stopOpacity={0.01}/></linearGradient></defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
          <XAxis dataKey="period" tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} minTickGap={34} tickFormatter={value => String(value).slice(2, 10)} tickLine={false} axisLine={false}/>
          <YAxis domain={domain} tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} tickFormatter={value => fmt(Number(value), digits)} width={68} tickLine={false} axisLine={false}/>
          <Tooltip formatter={(value: number) => [fmt(Number(value), digits), 'Close']} contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}/>
          <Area type="monotone" dataKey="value" stroke={color} fill="url(#timeSeriesFill)" strokeWidth={2} dot={false}/>
        </AreaChart>
      </ResponsiveContainer>}
  </div>;
}
