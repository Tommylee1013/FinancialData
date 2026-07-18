import React, { useState } from "react";
import { TrendingUp, TrendingDown, ChevronRight } from "lucide-react";
import { MiniLineChart, CandlestickChart } from "./CandlestickChart";
import {
  generateOHLC, marketIndices, volatilityIndices, macroVariables,
  commodities, globalBenchmarks
} from "../data/mockData";
import type { Tab } from "./NavBar";

const fmt = (v: number, d = 2) => v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

function PriceChange({ change, pct }: { change: number; pct: number }) {
  const up = change >= 0;
  return (
    <span className={`font-mono text-xs ${up ? 'text-up' : 'text-down'}`}>
      {up ? '+' : ''}{fmt(change)} ({up ? '+' : ''}{fmt(pct)}%)
    </span>
  );
}

function SectionHeader({ title, subtitle, onViewAll, onViewAllLabel = 'View All' }: {
  title: string; subtitle?: string; onViewAll?: () => void; onViewAllLabel?: string;
}) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <div className="w-0.5 h-4 bg-primary rounded-full" />
        <h2 className="text-sm font-bold text-foreground tracking-wide" style={{ fontFamily: 'Roboto Condensed, sans-serif' }}>{title}</h2>
        {subtitle && <span className="text-xs text-muted-foreground">{subtitle}</span>}
      </div>
      {onViewAll && (
        <button onClick={onViewAll} className="text-xs text-primary flex items-center gap-0.5 hover:underline">
          {onViewAllLabel} <ChevronRight size={12} />
        </button>
      )}
    </div>
  );
}

// ─── Global Benchmark Card (MSCI etc.) ────────────────────────────────────────
function BenchmarkCard({ bm }: { bm: typeof globalBenchmarks[0] }) {
  const up = bm.changePct >= 0;
  return (
    <div className="bg-card border border-border rounded p-4 flex flex-col gap-2 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-lg">{bm.flag}</span>
            <span className="text-xs font-bold text-foreground">{bm.name}</span>
          </div>
          <div className="text-[10px] text-muted-foreground mt-0.5">{bm.desc}</div>
        </div>
        <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded flex items-center gap-0.5 ${up ? 'bg-green-50 text-up dark:bg-green-950/30' : 'bg-red-50 text-down dark:bg-red-950/30'}`}>
          {up ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
          {up ? '+' : ''}{fmt(bm.changePct)}%
        </span>
      </div>
      <div>
        <div className="text-xl font-mono font-bold text-foreground">{fmt(bm.value)}</div>
        <PriceChange change={bm.change} pct={bm.changePct} />
      </div>
      <MiniLineChart data={bm.trend} width={200} height={44} color={up ? '#16A34A' : '#DC2626'} />
      <div className="flex justify-between text-[10px] font-mono text-muted-foreground border-t border-border pt-2">
        <span>YTD {bm.ytd >= 0 ? '+' : ''}{bm.ytd}%</span>
        <span>52W H: {fmt(bm.high52w)}</span>
        <span>L: {fmt(bm.low52w)}</span>
      </div>
    </div>
  );
}

// ─── Index Card ───────────────────────────────────────────────────────────────
function IndexCard({ idx, showCandle }: { idx: typeof marketIndices[0]; showCandle?: boolean }) {
  const [view, setView] = useState<'line' | 'candle'>('line');
  const ohlc = showCandle ? generateOHLC(idx.value * 0.95, 30, idx.value * 0.008) : null;
  const up = idx.changePct >= 0;

  return (
    <div className="bg-card border border-border rounded p-3 flex flex-col gap-1.5 hover:shadow-md transition-shadow h-full">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-sm">{idx.flag}</span>
            <span className="text-xs font-bold text-foreground">{idx.name}</span>
          </div>
          <div className="text-[10px] text-muted-foreground mt-0.5">Vol {idx.volume}</div>
        </div>
        <div className={`flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded font-mono ${up ? 'bg-green-50 text-up dark:bg-green-950/30' : 'bg-red-50 text-down dark:bg-red-950/30'}`}>
          {up ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
          {up ? '+' : ''}{fmt(idx.changePct)}%
        </div>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-sm font-mono font-bold text-foreground">{fmt(idx.value)}</div>
          <PriceChange change={idx.change} pct={idx.changePct} />
        </div>
        {showCandle && (
          <div className="flex gap-1">
            {(['line', 'candle'] as const).map(v => (
              <button key={v} onClick={() => setView(v)}
                className={`text-[9px] px-1 py-0.5 rounded ${view === v ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground'}`}>
                {v === 'line' ? 'Line' : 'Candle'}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="mt-0.5">
        {view === 'line' || !showCandle
          ? <MiniLineChart data={idx.trend} width={160} height={38} color={up ? '#16A34A' : '#DC2626'} />
          : ohlc && <CandlestickChart data={ohlc} width={160} height={46} />
        }
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
        <span>H: {fmt(idx.high)}</span>
        <span>L: {fmt(idx.low)}</span>
        <span>Prev: {fmt(idx.prev)}</span>
      </div>
    </div>
  );
}

// ─── Volatility Card ──────────────────────────────────────────────────────────
function VolCard({ v }: { v: typeof volatilityIndices[0] }) {
  const up = v.change >= 0;
  const fearColor = v.value < 15 ? 'text-up' : v.value < 25 ? 'text-yellow-500' : 'text-down';
  return (
    <div className="bg-card border border-border rounded p-3 flex gap-3 items-center hover:shadow-md transition-shadow">
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-0.5">
          <span className="text-xs font-bold text-foreground">{v.name}</span>
          <span className={`text-xs font-mono ${up ? 'text-up' : 'text-down'}`}>
            {up ? '+' : ''}{fmt(v.change)} ({up ? '+' : ''}{fmt(v.changePct)}%)
          </span>
        </div>
        <div className="text-[10px] text-muted-foreground mb-1">{v.desc}</div>
        <div className={`text-xl font-mono font-bold ${fearColor}`}>{fmt(v.value)}</div>
        <div className="flex justify-between text-[10px] text-muted-foreground font-mono mt-0.5">
          <span>H: {fmt(v.high)}</span>
          <span>L: {fmt(v.low)}</span>
        </div>
      </div>
      <MiniLineChart data={v.trend} width={72} height={38} color={up ? '#DC2626' : '#16A34A'} />
    </div>
  );
}

// ─── Macro Card ───────────────────────────────────────────────────────────────
function MacroCard({ m }: { m: typeof macroVariables[0] }) {
  const up = m.value > m.prev;
  const beat = m.value >= m.forecast;
  return (
    <div className="bg-card border border-border rounded p-3 hover:shadow-md transition-shadow h-full">
      <div className="flex items-start justify-between mb-1">
        <div>
          <div className="text-xs font-bold text-foreground">{m.name}</div>
          <div className="text-[10px] text-muted-foreground">{m.desc}</div>
          <div className="text-[10px] text-muted-foreground">{m.period}</div>
        </div>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${beat ? 'bg-green-100 text-up dark:bg-green-950/30' : 'bg-red-100 text-down dark:bg-red-950/30'}`}>
          {beat ? 'Beat' : 'Miss'}
        </span>
      </div>
      <div className="text-lg font-mono font-bold text-foreground">{fmt(m.value)}{m.unit}</div>
      <div className="flex gap-3 mt-1 text-[10px] font-mono text-muted-foreground">
        <span>Forecast <span className="text-foreground">{fmt(m.forecast)}{m.unit}</span></span>
        <span>Prev <span className="text-foreground">{fmt(m.prev)}{m.unit}</span></span>
      </div>
      <div className="mt-2">
        <MiniLineChart data={m.trend} width={140} height={34} color={up ? '#16A34A' : '#DC2626'} />
      </div>
    </div>
  );
}

// ─── Commodity Card ───────────────────────────────────────────────────────────
function CommodityCard({ c }: { c: typeof commodities[0] }) {
  const up = c.changePct >= 0;
  return (
    <div className="bg-card border border-border rounded p-3 flex items-center gap-3 hover:shadow-md transition-shadow">
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-bold text-foreground">{c.name}</div>
            <div className="text-[10px] text-muted-foreground">{c.category} · {c.unit}</div>
          </div>
          <span className={`text-xs font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
            {up ? '+' : ''}{fmt(c.changePct)}%
          </span>
        </div>
        <div className="text-sm font-mono font-bold text-foreground mt-0.5">{fmt(c.value)}</div>
        <div className="flex justify-between text-[10px] text-muted-foreground font-mono mt-0.5">
          <span>H: {fmt(c.high)}</span>
          <span>L: {fmt(c.low)}</span>
        </div>
      </div>
      <MiniLineChart data={c.trend} width={64} height={34} color={up ? '#16A34A' : '#DC2626'} />
    </div>
  );
}

// ─── Card Grid (fixed width, no stretching) ───────────────────────────────────
function CardGrid({ children, cardWidth = 190 }: { children: React.ReactNode; cardWidth?: number }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
      {children}
    </div>
  );
}

function FixedCard({ width, children }: { width: number; children: React.ReactNode }) {
  return (
    <div style={{ width, flexShrink: 0, flexGrow: 0 }}>
      {children}
    </div>
  );
}

// ─── Country Group ────────────────────────────────────────────────────────────
function IndexGroup({ label, items, cardWidth = 190 }: { label: string; items: typeof marketIndices; cardWidth?: number }) {
  return (
    <div>
      <div className="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">{label}</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {items.map(idx => (
          <div key={idx.id} style={{ width: cardWidth, flexShrink: 0 }}>
            <IndexCard idx={idx} showCandle />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export function MainDashboard({ setActiveTab }: { setActiveTab: (tab: Tab) => void }) {
  const usIdx   = marketIndices.filter(i => i.country === 'US');
  const krIdx   = marketIndices.filter(i => i.country === 'KR');
  const jpIdx   = marketIndices.filter(i => i.country === 'JP');
  const euIdx   = marketIndices.filter(i => ['DE','GB','FR'].includes(i.country));
  const asiaIdx = marketIndices.filter(i => ['HK','CN'].includes(i.country));

  return (
    <div className="p-4 space-y-6 max-w-screen-2xl mx-auto">

      {/* ── MSCI & Global Benchmarks 2×2 ── */}
      <section>
        <SectionHeader title="Global Benchmarks" subtitle="MSCI · DJ Commodity" />
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
          {globalBenchmarks.map(bm => (
            <BenchmarkCard key={bm.id} bm={bm} />
          ))}
        </div>
      </section>

      {/* ── Market Indices ── */}
      <section>
        <SectionHeader
          title="Global Market Indices"
          subtitle="By Country · Candlestick"
          onViewAll={() => setActiveTab('market')}
          onViewAllLabel="Market Tab →"
        />
        <div className="space-y-3">
          <IndexGroup label="🇺🇸 US" items={usIdx} cardWidth={195} />
          <IndexGroup label="🇰🇷 Korea" items={krIdx} cardWidth={195} />
          <IndexGroup label="🇯🇵 Japan" items={jpIdx} cardWidth={195} />
          <IndexGroup label="🇪🇺🇬🇧🇫🇷 Europe" items={euIdx} cardWidth={195} />
          <IndexGroup label="🌏 Asia" items={asiaIdx} cardWidth={195} />
        </div>
      </section>

      {/* ── Volatility ── */}
      <section>
        <SectionHeader
          title="Volatility Indices"
          subtitle="By Country"
          onViewAll={() => setActiveTab('market')}
          onViewAllLabel="Market Tab →"
        />
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {volatilityIndices.map(v => (
            <div key={v.id} style={{ width: 270, flexShrink: 0 }}>
              <VolCard v={v} />
            </div>
          ))}
        </div>
      </section>

      {/* ── Macro Variables ── */}
      <section>
        <SectionHeader
          title="Macro Variables"
          subtitle="CPI · PPI · PMI"
          onViewAll={() => setActiveTab('macro')}
          onViewAllLabel="Macro Tab →"
        />
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {macroVariables.map(m => (
            <div key={m.id} style={{ width: 185, flexShrink: 0 }}>
              <MacroCard m={m} />
            </div>
          ))}
        </div>
      </section>

      {/* ── Commodities ── */}
      <section>
        <SectionHeader
          title="Commodity Prices"
          subtitle="Energy · Precious Metals · Base Metals"
          onViewAll={() => setActiveTab('commodities')}
          onViewAllLabel="Commodities Tab →"
        />
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {commodities.map(c => (
            <div key={c.id} style={{ width: 248, flexShrink: 0 }}>
              <CommodityCard c={c} />
            </div>
          ))}
        </div>
      </section>

    </div>
  );
}
