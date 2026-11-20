import React, { useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { MiniLineChart, CandlestickChart } from "./CandlestickChart";
import {
  generateOHLC, marketIndices, volatilityIndices, macroVariables,
  commodities, globalBenchmarks
} from "../data/mockData";
import type { Tab } from "./NavBar";
import { openDetail } from "../detailNavigation";

const fmt = (v: number | null | undefined, d = 2) =>
  v == null ? '—' : v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

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
    <div className="mb-3 flex items-end justify-between">
      <div>
        <h2 className="text-sm font-semibold text-foreground tracking-tight">{title}</h2>
        {subtitle && <div className="mt-0.5 text-xs text-muted-foreground">{subtitle}</div>}
      </div>
      {onViewAll && (
        <button onClick={onViewAll} className="rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-secondary hover:text-foreground">
          {onViewAllLabel}
        </button>
      )}
    </div>
  );
}

// ─── Global Benchmark Card (MSCI etc.) ────────────────────────────────────────
function BenchmarkCard({ bm }: { bm: typeof globalBenchmarks[0] }) {
  const up = bm.changePct >= 0;
  return (
    <div onClick={() => openDetail('benchmark', bm.id)} className="bg-card border border-border rounded p-4 flex flex-col gap-2 hover:shadow-md transition-shadow cursor-pointer">
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
    <div onClick={() => openDetail('market', idx.id)} className="bg-card border border-border rounded p-3 flex flex-col gap-1.5 hover:shadow-md transition-shadow h-full cursor-pointer">
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
              <button key={v} onClick={(event) => { event.stopPropagation(); setView(v); }}
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
    <div onClick={() => openDetail('volatility', v.id)} className="bg-card border border-border rounded p-3 flex gap-3 items-center hover:shadow-md transition-shadow cursor-pointer">
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
    <div onClick={() => openDetail('macro', m.id)} className="bg-card border border-border rounded p-3 hover:shadow-md transition-shadow h-full cursor-pointer">
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
    <div onClick={() => openDetail('commodity', c.id)} className="bg-card border border-border rounded p-3 flex items-center gap-3 hover:shadow-md transition-shadow cursor-pointer">
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
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(auto-fit, minmax(${cardWidth}px, 1fr))` }}>
        {items.map(idx => (
          <div key={idx.id}>
            <IndexCard idx={idx} showCandle />
          </div>
        ))}
      </div>
    </div>
  );
}

function MarketPulse() {
  const ranked = [...marketIndices].sort((a, b) => b.changePct - a.changePct);
  const advances = marketIndices.filter(item => item.changePct >= 0).length;
  const average = marketIndices.reduce((sum, item) => sum + item.changePct, 0) / marketIndices.length;
  const vix = volatilityIndices.find(item => item.id === 'vix') ?? volatilityIndices[0];
  return <section className="grid grid-cols-2 overflow-hidden rounded-lg border border-border bg-card shadow-sm lg:grid-cols-4">
    {[{ label: 'Global breadth', value: `${advances} of ${marketIndices.length}`, note: 'indices advancing', tone: advances >= marketIndices.length / 2 ? 'text-up' : 'text-down' }, { label: 'Equal-weight move', value: `${average >= 0 ? '+' : ''}${fmt(average)}%`, note: 'global index basket', tone: average >= 0 ? 'text-up' : 'text-down' }, { label: 'Session leader', value: ranked[0].name, note: `+${fmt(ranked[0].changePct)}% today`, tone: 'text-foreground' }, { label: 'Volatility', value: `VIX ${fmt(vix.value)}`, note: vix.value < 15 ? 'low regime' : vix.value < 25 ? 'moderate regime' : 'high regime', tone: 'text-foreground' }].map((stat,index) => <div key={stat.label} className={`p-4 ${index % 2 ? 'border-l border-border':''} ${index >= 2 ? 'border-t border-border lg:border-t-0': ''} ${index === 2 ? 'lg:border-l':''}`}><div className="text-xs text-muted-foreground">{stat.label}</div><div className={`mt-2 truncate text-lg font-semibold tracking-tight ${stat.tone}`}>{stat.value}</div><div className="mt-1 text-xs text-muted-foreground">{stat.note}</div></div>)}
  </section>;
}

function RepresentativeMarkets() {
  const equity = marketIndices.find(item => item.id === 'sp500') ?? marketIndices[0];
  const bond = globalBenchmarks.find(item => item.id === 'bond' || /bond|aggregate/i.test(`${item.name} ${item.desc}`)) ?? globalBenchmarks[2] ?? globalBenchmarks[0];
  const commodity = globalBenchmarks.find(item => item.id === 'djci' || /commodity|gsci|crb/i.test(`${item.name} ${item.desc}`)) ?? globalBenchmarks[3] ?? globalBenchmarks[0];
  const volatility = volatilityIndices.find(item => item.id === 'vix') ?? volatilityIndices[0];
  const items = [
    { label: 'Equities', name: equity.name, value: equity.value, changePct: equity.changePct, trend: equity.trend, detail: () => openDetail('market', equity.id) },
    { label: 'Fixed income', name: bond.name, value: bond.value, changePct: bond.changePct, trend: bond.trend, detail: () => openDetail('benchmark', bond.id) },
    { label: 'Commodities', name: commodity.name, value: commodity.value, changePct: commodity.changePct, trend: commodity.trend, detail: () => openDetail('benchmark', commodity.id) },
    { label: 'Volatility', name: volatility.name, value: volatility.value, changePct: volatility.changePct, trend: volatility.trend, detail: () => openDetail('volatility', volatility.id) },
  ];
  return <section>
    <SectionHeader title="Cross-asset markets" subtitle="Representative indices across major asset classes" />
    <div className="grid grid-cols-1 overflow-hidden rounded-lg border border-border bg-card shadow-sm sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item,index) => {
        const up = item.changePct >= 0;
        return <button key={item.label} onClick={item.detail} className={`min-w-0 p-4 text-left hover:bg-secondary/40 ${index ? 'border-t border-border sm:border-t-0 sm:border-l':''} ${index === 2 ? 'sm:border-l-0 sm:border-t xl:border-l xl:border-t-0':''}`}>
          <div className="flex items-start justify-between gap-3"><div><div className="text-[11px] font-medium text-muted-foreground">{item.label}</div><div className="mt-1 text-sm font-semibold">{item.name}</div></div><span className={`text-xs font-semibold tabular-nums ${up?'text-up':'text-down'}`}>{up?'+':''}{fmt(item.changePct)}%</span></div>
          <div className="mt-3 text-xl font-semibold tracking-tight tabular-nums">{fmt(item.value)}</div>
          <div className="mt-3 overflow-hidden"><MiniLineChart data={item.trend.slice(-45)} width={240} height={54} color={up?'#2563EB':'#DC2626'} fill={false}/></div>
        </button>;
      })}
    </div>
  </section>;
}

function BenchmarkBoard() {
  return <div className="bg-card border border-border rounded-lg overflow-hidden shadow-sm">
    <div className="grid grid-cols-[minmax(180px,1.5fr)_110px_100px_100px_100px_100px_minmax(120px,1fr)] px-4 py-2 bg-secondary/70 border-b border-border text-[9px] uppercase tracking-wider text-muted-foreground font-semibold">
      <span>Benchmark</span><span className="text-right">Last</span><span className="text-right">Change</span><span className="text-right">YTD</span><span className="text-right">52W High</span><span className="text-right">52W Low</span><span className="text-right">Trend</span>
    </div>
    {globalBenchmarks.map((bm, index) => {
      const up = bm.changePct >= 0;
      return <button key={bm.id} onClick={() => openDetail('benchmark', bm.id)} className={`w-full grid grid-cols-[minmax(180px,1.5fr)_110px_100px_100px_100px_100px_minmax(120px,1fr)] items-center px-4 py-2.5 text-xs text-left hover:bg-accent transition-colors ${index ? 'border-t border-border' : ''}`}>
        <span className="flex items-center gap-2 min-w-0"><span className="text-base">{bm.flag}</span><span className="min-w-0"><span className="block font-semibold truncate">{bm.name}</span><span className="block text-[9px] text-muted-foreground truncate">{bm.desc}</span></span></span>
        <span className="text-right font-mono font-bold">{fmt(bm.value)}</span>
        <span className={`text-right font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>{up ? '+' : ''}{fmt(bm.changePct)}%</span>
        <span className={`text-right font-mono ${bm.ytd >= 0 ? 'text-up' : 'text-down'}`}>{bm.ytd >= 0 ? '+' : ''}{fmt(bm.ytd)}%</span>
        <span className="text-right font-mono text-muted-foreground">{fmt(bm.high52w)}</span>
        <span className="text-right font-mono text-muted-foreground">{fmt(bm.low52w)}</span>
        <span className="flex justify-end"><MiniLineChart data={bm.trend} width={110} height={28} color={up ? '#16A34A' : '#DC2626'} fill={false}/></span>
      </button>;
    })}
  </div>;
}

function MarketQuoteBoard({ groups }: { groups: Array<{ label: string; items: typeof marketIndices }> }) {
  return <div className="bg-card border border-border rounded-lg overflow-hidden shadow-sm">
    <div className="hidden md:grid grid-cols-[minmax(170px,1.4fr)_115px_105px_105px_105px_105px_105px_minmax(100px,1fr)] px-4 py-2 bg-secondary/70 border-b border-border text-[9px] uppercase tracking-wider text-muted-foreground font-semibold">
      <span>Index</span><span className="text-right">Last</span><span className="text-right">Change</span><span className="text-right">Change %</span><span className="text-right">High</span><span className="text-right">Low</span><span className="text-right">Volume</span><span className="text-right">30D Trend</span>
    </div>
    <div className="max-h-[443px] overflow-y-auto">{groups.map(group => <React.Fragment key={group.label}>
      <div className="px-4 py-2 bg-secondary/40 border-t first:border-t-0 border-border text-[10px] font-semibold text-muted-foreground">{group.label}</div>
      {group.items.map(idx => {
        const up = idx.changePct >= 0;
        return <button key={idx.id} onClick={() => openDetail('market', idx.id)} className="w-full md:grid md:grid-cols-[minmax(170px,1.4fr)_115px_105px_105px_105px_105px_105px_minmax(100px,1fr)] flex items-center justify-between px-4 py-2.5 border-t border-border hover:bg-accent transition-colors text-xs text-left group">
          <span className="flex items-center gap-2 min-w-0"><span>{idx.flag}</span><span><span className="block font-semibold group-hover:text-primary">{idx.name}</span><span className="block md:hidden text-[9px] text-muted-foreground">{idx.country}</span></span></span>
          <span className="text-right font-mono font-bold">{fmt(idx.value)}</span>
          <span className={`hidden md:block text-right font-mono ${up ? 'text-up' : 'text-down'}`}>{up ? '+' : ''}{fmt(idx.change)}</span>
          <span className={`text-right font-mono font-bold ${up ? 'text-up' : 'text-down'}`}>{up ? '+' : ''}{fmt(idx.changePct)}%</span>
          <span className="hidden md:block text-right font-mono text-muted-foreground">{fmt(idx.high)}</span>
          <span className="hidden md:block text-right font-mono text-muted-foreground">{fmt(idx.low)}</span>
          <span className="hidden md:block text-right font-mono text-muted-foreground">{idx.volume}</span>
          <span className="hidden md:flex justify-end"><MiniLineChart data={idx.trend.slice(-30)} width={100} height={26} color={up ? '#16A34A' : '#DC2626'} fill={false}/></span>
        </button>;
      })}
    </React.Fragment>)}</div>
  </div>;
}

function MarketSignals() {
  return <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
    <div className="border-b border-border px-4 py-3"><h2 className="text-sm font-semibold">Market signals</h2><p className="mt-0.5 text-xs text-muted-foreground">Volatility and macro releases</p></div>
    <div className="px-4 py-2">{volatilityIndices.slice(0,4).map(v => {
      const up = v.change >= 0;
      return <button key={v.id} onClick={() => openDetail('volatility', v.id)} className="flex w-full items-center justify-between border-b border-border py-3 text-left last:border-0 hover:text-primary"><span><span className="block text-xs font-medium">{v.name}</span><span className="mt-0.5 block text-[11px] text-muted-foreground">{v.desc}</span></span><span className="text-right"><b className="block text-sm tabular-nums">{fmt(v.value)}</b><span className={`text-[11px] tabular-nums ${up ? 'text-up':'text-down'}`}>{up?'+':''}{fmt(v.changePct)}%</span></span></button>;
    })}</div>
    <div className="border-y border-border bg-secondary/35 px-4 py-2 text-[11px] font-medium text-muted-foreground">Latest macro releases</div>
    <div className="px-4 py-1">{macroVariables.slice(0,4).map(m => <button key={m.id} onClick={() => openDetail('macro',m.id)} className="flex w-full items-center justify-between border-b border-border py-2.5 text-left last:border-0"><span><span className="block text-xs font-medium">{m.name}</span><span className="text-[11px] text-muted-foreground">{m.period}</span></span><span className="text-right"><b className="block text-xs tabular-nums">{fmt(m.value)}{m.unit}</b><span className="text-[10px] text-muted-foreground">Est. {fmt(m.forecast)}{m.unit}</span></span></button>)}</div>
  </div>;
}

function CompactOverviewList({ type }: { type: 'macro' | 'commodities' }) {
  const isMacro = type === 'macro';
  return <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
    <div className="grid grid-cols-[1fr_90px_90px_90px] border-b border-border bg-secondary/45 px-4 py-2 text-[10px] font-medium text-muted-foreground"><span>{isMacro ? 'Indicator':'Commodity'}</span><span className="text-right">Last</span><span className="text-right">Previous</span><span className="text-right">Change</span></div>
    {isMacro ? macroVariables.slice(0,6).map(m => {
      const delta = m.value - m.prev;
      return <button key={m.id} onClick={() => openDetail('macro',m.id)} className="grid w-full grid-cols-[1fr_90px_90px_90px] items-center border-b border-border px-4 py-3 text-left text-xs last:border-0 hover:bg-secondary/50"><span><b className="block font-medium">{m.name}</b><span className="text-[11px] text-muted-foreground">{m.period}</span></span><span className="text-right tabular-nums">{fmt(m.value)}{m.unit}</span><span className="text-right tabular-nums text-muted-foreground">{fmt(m.prev)}{m.unit}</span><span className={`text-right tabular-nums ${delta >= 0?'text-up':'text-down'}`}>{delta>=0?'+':''}{fmt(delta)}{m.unit}</span></button>;
    }) : commodities.slice(0,6).map(c => <button key={c.id} onClick={() => openDetail('commodity',c.id)} className="grid w-full grid-cols-[1fr_90px_90px_90px] items-center border-b border-border px-4 py-3 text-left text-xs last:border-0 hover:bg-secondary/50"><span><b className="block font-medium">{c.name}</b><span className="text-[11px] text-muted-foreground">{c.unit}</span></span><span className="text-right tabular-nums">{fmt(c.value)}</span><span className="text-right tabular-nums text-muted-foreground">{fmt(c.prev)}</span><span className={`text-right tabular-nums ${c.changePct>=0?'text-up':'text-down'}`}>{c.changePct>=0?'+':''}{fmt(c.changePct)}%</span></button>)}
  </div>;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export function MainDashboard({ setActiveTab }: { setActiveTab: (tab: Tab) => void }) {
  const usIdx   = marketIndices.filter(i => i.country === 'US');
  const krIdx   = marketIndices.filter(i => i.country === 'KR');
  const jpIdx   = marketIndices.filter(i => i.country === 'JP');
  const euIdx   = marketIndices.filter(i => ['DE','GB','FR'].includes(i.country));
  const asiaIdx = marketIndices.filter(i => ['HK','CN'].includes(i.country));

  return (
    <div className="mx-auto max-w-screen-2xl space-y-6 p-4 sm:p-6">

      <MarketPulse />

      <RepresentativeMarkets />

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div>
        <SectionHeader
          title="Markets"
          subtitle="Major indices by region"
          onViewAll={() => setActiveTab('market')}
          onViewAllLabel="View market"
        />
        <MarketQuoteBoard groups={[
          { label: 'United States', items: usIdx },
          { label: 'South Korea', items: krIdx },
          { label: 'Japan', items: jpIdx },
          { label: 'Europe', items: euIdx },
          { label: 'Greater China', items: asiaIdx },
        ]} />
        </div>
        <div><div className="mb-3"><h2 className="text-sm font-semibold">Today</h2><div className="mt-0.5 text-xs text-muted-foreground">Risk and economic context</div></div><MarketSignals /></div>
      </section>

      <section>
        <SectionHeader title="Global benchmarks" subtitle="Equity, fixed income and commodity baskets" />
        <BenchmarkBoard />
      </section>

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <div><SectionHeader title="Macro monitor" subtitle="Latest releases against previous readings" onViewAll={() => setActiveTab('macro')} onViewAllLabel="View macro"/><CompactOverviewList type="macro"/></div>
        <div><SectionHeader title="Commodities" subtitle="Energy, metals and agricultural markets" onViewAll={() => setActiveTab('commodities')} onViewAllLabel="View commodities"/><CompactOverviewList type="commodities"/></div>
      </section>

    </div>
  );
}
