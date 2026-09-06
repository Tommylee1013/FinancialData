import React, { useState } from 'react';
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Bot, CalendarDays, Database, Gauge, Layers3 } from 'lucide-react';
import type { DetailKind } from '../detailNavigation';
import { TimeSeriesChart } from './TimeSeriesChart';
import {
  commodities, dashboardConnection, freightIndices, globalBenchmarks,
  industryData, macroVariables, marketIndices, volatilityIndices,
  yieldCurveUS, yieldCurveKR, krSwapRates, moneyMarket, sectorDataByCountry, sentimentData,
} from '../data/mockData';

const fixedIncomeItems = [
  ...yieldCurveUS.map(item => ({ ...item, id: `us-${item.tenor.toLowerCase()}`, name: `US Treasury ${item.tenor}`, value: item.yield, country: 'United States', flag: '🇺🇸', unit: '%', category: 'Government Bond' })),
  ...yieldCurveKR.map(item => ({ ...item, id: `kr-${item.tenor.toLowerCase()}`, name: `Korea Treasury ${item.tenor}`, value: item.yield, country: 'South Korea', flag: '🇰🇷', unit: '%', category: 'Government Bond' })),
  ...krSwapRates.flatMap(item => [
    { id: `kr-irs-${item.tenor.toLowerCase()}`, name: `Korea IRS ${item.tenor}`, value: item.irs, prev: item.irs - item.irsChange, change: item.irsChange, country: 'South Korea', flag: '🇰🇷', unit: '%', category: 'Interest Rate Swap' },
    { id: `kr-crs-${item.tenor.toLowerCase()}`, name: `Korea CRS ${item.tenor}`, value: item.crs, prev: item.crs - item.crsChange, change: item.crsChange, country: 'South Korea', flag: '🇰🇷', unit: '%', category: 'Cross-Currency Swap' },
  ]),
  ...moneyMarket.map((item, index) => ({ ...item, id: `money-${index}`, name: item.name, prev: item.value - item.change, country: item.flag, unit: '%', category: 'Money Market' })),
];

const collections: Record<DetailKind, any[]> = {
  benchmark: globalBenchmarks,
  market: marketIndices,
  volatility: volatilityIndices,
  macro: macroVariables,
  commodity: commodities,
  freight: freightIndices,
  industry: industryData,
  'fixed-income': fixedIncomeItems,
  sector: Object.values(sectorDataByCountry).flat(),
  sentiment: [],
};

function getCollection(kind: DetailKind) {
  if (kind !== 'sentiment') return collections[kind];
  return [
    { ...sentimentData.fng, id: 'fear-greed', name: 'CNN Fear & Greed Index', category: 'Market Sentiment', unit: 'pt' },
    { ...sentimentData.aaii, id: 'aaii', name: 'AAII Bullish Sentiment', category: 'Investor Survey', unit: '%' },
    { ...sentimentData.naaim, id: 'naaim', name: 'NAAIM Exposure Index', category: 'Manager Exposure', unit: '%' },
  ];
}

const labels: Record<DetailKind, string> = {
  benchmark: 'GLOBAL BENCHMARK', market: 'MARKET INDEX', volatility: 'VOLATILITY',
  macro: 'MACRO INDICATOR', commodity: 'COMMODITY', freight: 'FREIGHT INDEX', industry: 'INDUSTRY DATA',
  'fixed-income': 'FIXED INCOME',
  sector: 'SECTOR INDEX',
  sentiment: 'MARKET SENTIMENT',
};

const fmt = (value: number | null | undefined, digits = 2) =>
  value == null ? '—' : value.toLocaleString('en-US', { maximumFractionDigits: digits });

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return <div className="border-r border-border last:border-r-0 px-4 py-3">
    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
    <div className="mt-1 text-lg font-mono font-semibold text-foreground">{value}</div>
    {note && <div className="mt-0.5 text-[10px] text-muted-foreground">{note}</div>}
  </div>;
}

export function DetailPage({ kind, id, onBack, onAskAI }: { kind: DetailKind; id: string; onBack: () => void; onAskAI?: (context: Record<string, unknown>) => void }) {
  const [range, setRange] = useState<'1M' | '3M' | '6M' | '1Y' | 'MAX' | 'CUSTOM'>('6M');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const item = getCollection(kind)?.find(entry => entry.id === id);
  if (!item) return <div className="p-10 text-center"><p className="text-muted-foreground">This indicator could not be found.</p><button className="mt-4 text-primary" onClick={onBack}>Go back</button></div>;

  const change = item.change ?? (item.value != null && item.prev != null ? item.value - item.prev : 0);
  const changePct = item.changePct ?? (item.prev ? change / item.prev * 100 : 0);
  const up = change >= 0;
  const rawTrend = item.ohlc?.length ? item.ohlc : item.trend?.length ? item.trend : Array.from({ length: 24 }, (_, i) => ({ t: i, v: item.value ?? 0 }));
  const fullSeries = rawTrend.map((point: any, index: number) => {
    const fallback = new Date();
    fallback.setDate(fallback.getDate() - (rawTrend.length - 1 - index));
    const date = point.date ?? fallback.toISOString().slice(0, 10);
    return { period: date, date, value: point.v ?? point.value ?? point.close,
      open: point.open, high: point.high, low: point.low, close: point.close };
  });
  const series = (() => {
    if (range === 'MAX') return fullSeries;
    const latest = new Date(fullSeries.at(-1)?.date ?? Date.now());
    let start: Date;
    let end = latest;
    if (range === 'CUSTOM') {
      start = customStart ? new Date(customStart) : new Date(fullSeries[0]?.date ?? latest);
      end = customEnd ? new Date(customEnd) : latest;
    } else {
      start = new Date(latest);
      const months = range === '1M' ? 1 : range === '3M' ? 3 : range === '6M' ? 6 : 12;
      start.setMonth(start.getMonth() - months);
    }
    return fullSeries.filter((point: any) => {
      const date = new Date(point.date);
      return date >= start && date <= end;
    });
  })();
  const visibleSeries = series.length ? series : fullSeries;
  const values = visibleSeries.map((p: any) => p.value).filter((v: any) => typeof v === 'number');
  const high = item.high ?? item.high52w ?? (values.length ? Math.max(...values) : item.value);
  const low = item.low ?? item.low52w ?? (values.length ? Math.min(...values) : item.value);
  const previous = item.prev ?? (series.length > 1 ? series[series.length - 2].value : item.value);
  const unit = item.unit ?? (kind === 'macro' ? item.unit : kind === 'volatility' || kind === 'market' ? 'pt' : '');

  return <div className="max-w-screen-2xl mx-auto p-4 md:p-6 space-y-4">
    <button onClick={onBack} className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
      <ArrowLeft size={14}/> Overview
    </button>

    <section className="bg-card border border-border rounded-lg overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-border flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="text-[10px] font-semibold tracking-[0.16em] text-primary">{labels[kind]}</div>
          <div className="flex items-center gap-2 mt-1">
            {item.flag && <span className="text-xl">{item.flag}</span>}
            <h1 className="text-2xl font-bold tracking-tight text-foreground">{item.name}</h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-secondary text-muted-foreground uppercase">{id}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">{item.desc ?? item.fullName ?? item.category ?? 'Financial market time series'}</p>
        </div>
        <div className="md:text-right">
          <div className="text-3xl font-mono font-bold text-foreground">{fmt(item.value)} <span className="text-xs font-normal text-muted-foreground">{unit}</span></div>
          <div className={`mt-1 inline-flex items-center gap-1 font-mono text-sm font-semibold ${up ? 'text-up' : 'text-down'}`}>
            {up ? <ArrowUpRight size={15}/> : <ArrowDownRight size={15}/>}{up ? '+' : ''}{fmt(change)} ({up ? '+' : ''}{fmt(changePct)}%)
          </div>
          {onAskAI && <button onClick={() => onAskAI({ kind, id, name: item.name, value: item.value, asOf: item.asOf ?? item.period })} className="mt-3 inline-flex items-center gap-1.5 rounded bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground"><Bot size={13}/>Ask AI</button>}
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 bg-secondary/30">
        <Stat label="Previous" value={fmt(previous)} note="Previous observation"/>
        <Stat label="Period High" value={fmt(high)} note="Visible time window"/>
        <Stat label="Period Low" value={fmt(low)} note="Visible time window"/>
        <Stat label="Range" value={fmt((high ?? 0) - (low ?? 0))} note={item.period ?? item.asOf ?? 'Latest available'}/>
      </div>
    </section>

    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <section className="xl:col-span-2 bg-card border border-border rounded-lg p-4 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-3 mb-5">
          <div><h2 className="text-sm font-bold">Price / Value History</h2><p className="text-[10px] text-muted-foreground mt-0.5">Latest {series.length} observations</p></div>
          <div className="flex flex-wrap items-center gap-1">
            {(['1M','3M','6M','1Y','MAX'] as const).map(option => <button key={option} onClick={() => setRange(option)} className={`text-[10px] px-2 py-1 rounded border ${range === option ? 'bg-primary text-primary-foreground border-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>{option}</button>)}
            <button onClick={() => setRange('CUSTOM')} className={`text-[10px] px-2 py-1 rounded border ${range === 'CUSTOM' ? 'bg-primary text-primary-foreground border-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>CUSTOM</button>
          </div>
        </div>
        {range === 'CUSTOM' && <div className="flex flex-wrap items-center gap-2 mb-4 p-2.5 bg-secondary/50 border border-border rounded text-[10px]"><span className="font-semibold text-muted-foreground">Date range</span><input aria-label="Start date" type="date" value={customStart} onChange={e => setCustomStart(e.target.value)} className="bg-card border border-border rounded px-2 py-1 text-foreground"/><span className="text-muted-foreground">to</span><input aria-label="End date" type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)} className="bg-card border border-border rounded px-2 py-1 text-foreground"/></div>}
        <TimeSeriesChart data={visibleSeries} height={330} color={up ? '#16A34A' : '#DC2626'} digits={kind === 'fixed-income' ? 3 : 2}/>
      </section>

      <aside className="space-y-4">
        <section className="bg-card border border-border rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-bold mb-3">Research Snapshot</h2>
          <div className="space-y-3 text-xs">
            <div className="flex gap-3"><Gauge size={15} className="text-primary shrink-0"/><div><div className="font-semibold">Momentum</div><div className="text-muted-foreground mt-0.5">The latest move is <span className={up ? 'text-up' : 'text-down'}>{up ? 'upward' : 'downward'}</span>, with a change of {fmt(Math.abs(changePct))}%.</div></div></div>
            <div className="flex gap-3"><Layers3 size={15} className="text-primary shrink-0"/><div><div className="font-semibold">Classification</div><div className="text-muted-foreground mt-0.5">{item.category ?? labels[kind]} · {item.country ?? item.type ?? 'Global'}</div></div></div>
            <div className="flex gap-3"><CalendarDays size={15} className="text-primary shrink-0"/><div><div className="font-semibold">Observation</div><div className="text-muted-foreground mt-0.5">{item.asOf ?? item.period ?? dashboardConnection.updatedAt ?? 'Latest available'}</div></div></div>
            <div className="flex gap-3"><Database size={15} className="text-primary shrink-0"/><div><div className="font-semibold">Data Source</div><div className="text-muted-foreground mt-0.5">{dashboardConnection.connected ? 'Local DuckDB · read-only' : 'Bundled demo fallback'}</div></div></div>
          </div>
        </section>
        <section className="bg-card border border-border rounded-lg overflow-hidden shadow-sm">
          <div className="px-4 py-3 border-b border-border"><h2 className="text-sm font-bold">Recent Observations</h2></div>
          <div className="divide-y divide-border">
            {visibleSeries.slice(-6).reverse().map((point: any, index: number) => <div key={index} className="flex justify-between px-4 py-2 text-xs"><span className="text-muted-foreground font-mono">{String(point.period)}</span><span className="font-mono font-semibold">{fmt(point.value)}</span></div>)}
          </div>
        </section>
      </aside>
    </div>
    <p className="text-[10px] text-muted-foreground">Research interface only. Values may be delayed or incomplete and are not investment advice.</p>
  </div>;
}
