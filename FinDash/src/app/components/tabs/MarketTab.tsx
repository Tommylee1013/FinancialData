import React, { useState } from "react";
import { ChevronRight, Newspaper } from "lucide-react";
import { MiniLineChart } from "../CandlestickChart";
import { TradingViewChart } from "../TradingViewChart";
import {
  marketIndices, volatilityIndices, sectorDataByCountry,
  newsFeed, sentimentData, generateOHLC
} from "../../data/mockData";
import { openDetail } from "../../detailNavigation";

const fmt = (v: number | null | undefined, d = 2) => v == null ? '—' : v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

const countries = [
  { id: 'ALL', label: 'All Markets', flag: '🌐', indexCountries: ['US', 'KR', 'JP', 'CN', 'HK', 'DE', 'GB', 'FR'] },
  { id: 'US', label: 'United States', flag: '🇺🇸', indexCountries: ['US'] },
  { id: 'KR', label: 'South Korea', flag: '🇰🇷', indexCountries: ['KR'] },
  { id: 'JP', label: 'Japan', flag: '🇯🇵', indexCountries: ['JP'] },
  { id: 'CN', label: 'Greater China', flag: '🇨🇳', indexCountries: ['CN', 'HK'] },
] as const;

function FngGauge({ value, label }: { value: number; label: string }) {
  const pct = Math.max(0, Math.min(100, value)) / 100;
  const color = value < 25 ? '#DC2626' : value < 45 ? '#F97316' : value < 55 ? '#EAB308' : value < 75 ? '#84CC16' : '#16A34A';
  const cx = 80, cy = 72, r = 58;
  const startAngle = -180; const endAngle = 0;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const arcPath = (s: number, e: number) => {
    const x1 = cx + r * Math.cos(toRad(s));
    const y1 = cy + r * Math.sin(toRad(s));
    const x2 = cx + r * Math.cos(toRad(e));
    const y2 = cy + r * Math.sin(toRad(e));
    return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`;
  };
  const needleX = cx + (r - 8) * Math.cos(toRad(startAngle + pct * 180));
  const needleY = cy + (r - 8) * Math.sin(toRad(startAngle + pct * 180));

  return (
    <div className="flex min-h-[178px] flex-col items-center justify-start pt-1">
      <svg width={160} height={78} className="overflow-visible" aria-label={`Fear and Greed Index: ${value}`}>
        <path d={arcPath(-180, 0)} fill="none" stroke="var(--muted)" strokeWidth={12} />
        <path d={arcPath(-180, startAngle + pct * 180)} fill="none" stroke={color} strokeWidth={12} />
        <line x1={cx} y1={cy} x2={needleX} y2={needleY} stroke="var(--foreground)" strokeWidth={2} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={4} fill="var(--foreground)" />
      </svg>
      <div className="mt-2 font-mono text-2xl font-bold leading-none" style={{ color }}>{fmt(value, 2)}</div>
      <span className="mt-2 text-sm font-semibold leading-none" style={{ color }}>{label}</span>
      <span className="mt-2 text-xs text-muted-foreground">CNN Fear &amp; Greed Index</span>
    </div>
  );
}

export function MarketTab() {
  const [country, setCountry] = useState<string>('ALL');
  const [selectedIdx, setSelectedIdx] = useState(marketIndices[0]);
  const countryConfig = countries.find(item => item.id === country) ?? countries[0];
  const filteredIndices = marketIndices.filter(index => countryConfig.indexCountries.includes(index.country as never));
  const sectors = sectorDataByCountry[country] ?? [];
  const selectCountry = (next: typeof countries[number]) => {
    setCountry(next.id);
    const first = marketIndices.find(index => next.indexCountries.includes(index.country as never));
    if (first) setSelectedIdx(first);
  };
  const ohlcData = (selectedIdx as any).ohlc?.length ? (selectedIdx as any).ohlc : generateOHLC(selectedIdx.value * 0.92, 60, selectedIdx.value * 0.01);

  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      <div className="bg-card border border-border rounded p-1 flex gap-1 overflow-x-auto">
        {countries.map(item => <button key={item.id} onClick={() => selectCountry(item)} className={`px-4 py-2 rounded text-xs font-semibold whitespace-nowrap transition-colors ${country === item.id ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'}`}>
          <span className="mr-1.5">{item.flag}</span>{item.label}
        </button>)}
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">

        {/* Left: Index selector + chart */}
        <div className="xl:col-span-2 space-y-3">
          {/* Index list */}
          <div className="bg-card border border-border rounded overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-secondary">
                  <tr>
                    {['Index', 'Price', 'Change', 'Change%', '52W High', '52W Low', 'Volume', 'Chart'].map(h => (
                      <th key={h} className="text-left px-3 py-2 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredIndices.map(idx => {
                    const up = idx.changePct >= 0;
                    const selected = idx.id === selectedIdx.id;
                    return (
                      <tr
                        key={idx.id}
                        onClick={() => setSelectedIdx(idx)}
                        className={`border-t border-border cursor-pointer transition-colors ${selected ? 'bg-accent' : 'hover:bg-secondary'}`}
                      >
                        <td className="px-3 py-1.5 font-semibold text-foreground whitespace-nowrap">
                          <span className="mr-1">{idx.flag}</span>{idx.name}
                        </td>
                        <td className="px-3 py-1.5 font-mono text-foreground">{fmt(idx.value)}</td>
                        <td className={`px-3 py-1.5 font-mono ${up ? 'text-up' : 'text-down'}`}>
                          {up ? '+' : ''}{fmt(idx.change)}
                        </td>
                        <td className={`px-3 py-1.5 font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
                          {up ? '+' : ''}{fmt(idx.changePct)}%
                        </td>
                        <td className="px-3 py-1.5 font-mono text-muted-foreground">{fmt(idx.high)}</td>
                        <td className="px-3 py-1.5 font-mono text-muted-foreground">{fmt(idx.low)}</td>
                        <td className="px-3 py-1.5 text-muted-foreground">{idx.volume}</td>
                        <td className="px-3 py-1.5">
                          <MiniLineChart data={idx.trend} width={60} height={22} color={up ? '#16A34A' : '#DC2626'} fill={false} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Candlestick Chart */}
          <div className="bg-card border border-border rounded p-3">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="text-sm font-bold text-foreground">{selectedIdx.flag} {selectedIdx.name}</span>
                <span className="ml-2 font-mono text-sm font-bold text-foreground">{fmt(selectedIdx.value)}</span>
                <span className={`ml-2 text-xs font-mono ${selectedIdx.changePct >= 0 ? 'text-up' : 'text-down'}`}>
                  {selectedIdx.changePct >= 0 ? '+' : ''}{fmt(selectedIdx.changePct)}%
                </span>
              </div>
              <div className="text-[10px] text-muted-foreground bg-accent px-2 py-0.5 rounded">
                TradingView Lightweight Charts · Scroll to zoom
              </div>
            </div>
            <TradingViewChart data={ohlcData} height={480} initialMonths={3} />
          </div>

          {/* Country sector board */}
          {country !== 'ALL' && <div className="bg-card border border-border rounded overflow-hidden">
            <div className="px-3 py-2.5 border-b border-border flex items-center justify-between">
              <div><div className="text-xs font-bold text-foreground">{countryConfig.flag} {countryConfig.label} Sector Performance</div><div className="text-[10px] text-muted-foreground mt-0.5">Select a sector for price history and detailed statistics</div></div>
              <span className="text-[10px] font-mono text-muted-foreground">{sectors.length} SECTORS</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead className="bg-secondary/60 text-muted-foreground"><tr><th className="text-left px-3 py-2">Sector</th><th className="text-right px-3 py-2">Last</th><th className="text-right px-3 py-2">Change</th><th className="text-right px-3 py-2">Change %</th><th className="text-right px-3 py-2">Range</th><th className="px-3 py-2"></th></tr></thead>
                <tbody>{sectors.map((sector: any) => {
                  const up = (sector.changePct ?? 0) >= 0;
                  return <tr key={sector.id ?? sector.name} onClick={() => openDetail('sector', sector.id)} className="border-t border-border cursor-pointer hover:bg-accent transition-colors">
                    <td className="px-3 py-2"><div className="font-semibold text-foreground">{sector.name}</div><div className="text-[9px] text-muted-foreground">{sector.symbol ?? sector.category ?? 'Sector index'}</div></td>
                    <td className="px-3 py-2 text-right font-mono">{fmt(sector.value)}</td>
                    <td className={`px-3 py-2 text-right font-mono ${up ? 'text-up' : 'text-down'}`}>{sector.change != null && up ? '+' : ''}{fmt(sector.change)}</td>
                    <td className={`px-3 py-2 text-right font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>{up ? '+' : ''}{fmt(sector.changePct)}%</td>
                    <td className="px-3 py-2 text-right font-mono text-muted-foreground">{fmt(sector.low)} – {fmt(sector.high)}</td>
                    <td className="px-3 py-2 text-muted-foreground"><ChevronRight size={13}/></td>
                  </tr>;
                })}</tbody>
              </table>
              {!sectors.length && <div className="p-8 text-center text-xs text-muted-foreground">No sector series available for this market.</div>}
            </div>
          </div>}
        </div>

        {/* Right: Volatility + Sentiment + News */}
        <div className="space-y-3">

          {/* Volatility */}
          <div className="bg-card border border-border rounded p-3">
            <div className="text-xs font-bold text-foreground mb-2">Volatility Indices</div>
            <div className="space-y-2">
              {volatilityIndices.map(v => {
                const up = v.change >= 0;
                const lvl = v.value < 15 ? 'Low' : v.value < 25 ? 'Moderate' : 'High';
                const lvlColor = v.value < 15 ? 'text-up' : v.value < 25 ? 'text-yellow-500' : 'text-down';
                return (
                  <div key={v.id} onClick={() => openDetail('volatility', v.id)} className="flex items-center justify-between py-1 border-b border-border last:border-0 cursor-pointer hover:bg-accent px-1 rounded">
                    <div>
                      <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">{v.name}<span className={`text-[8px] px-1 rounded ${(v as any).asOf ? 'bg-green-500/10 text-up' : 'bg-secondary text-muted-foreground'}`}>{(v as any).asOf ? 'DB' : 'SAMPLE'}</span></div>
                      <div className="text-[10px] text-muted-foreground">{v.desc}</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-mono font-bold ${lvlColor}`}>{fmt(v.value)}</div>
                      <div className={`text-[10px] font-mono ${up ? 'text-up' : 'text-down'}`}>
                        {up ? '+' : ''}{fmt(v.change)} <span className={lvlColor}>({lvl})</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Sentiment */}
          <div className="bg-card border border-border rounded p-3">
            <div className="text-xs font-bold text-foreground mb-3">Market Sentiment Indicators</div>
            <div onClick={() => openDetail('sentiment', 'fear-greed')} className="flex justify-center mb-3 rounded cursor-pointer hover:bg-accent transition-colors" role="button" tabIndex={0}>
              {sentimentData.fng.connected !== false ? <FngGauge value={sentimentData.fng.value ?? 0} label={sentimentData.fng.label} /> : <div className="py-6 text-xs text-muted-foreground">Fear &amp; Greed data unavailable</div>}
            </div>
            <div className="space-y-2 border-t border-border pt-2">
              <div onClick={() => openDetail('sentiment', 'aaii')} className="rounded p-1 cursor-pointer hover:bg-accent transition-colors" role="button" tabIndex={0}>
              <div className="text-[10px] font-semibold text-muted-foreground mb-1 flex items-center justify-between"><span>AAII Sentiment Survey</span><ChevronRight size={12}/></div>
              <div className="flex gap-2 text-[11px]">
                <div className="flex-1 text-center">
                  <div className="text-up font-mono font-bold">{fmt(sentimentData.aaii.bullish, 1)}%</div>
                  <div className="text-muted-foreground">Bullish</div>
                </div>
                <div className="flex-1 text-center">
                  <div className="text-muted-foreground font-mono font-bold">{fmt(sentimentData.aaii.neutral, 1)}%</div>
                  <div className="text-muted-foreground">Neutral</div>
                </div>
                <div className="flex-1 text-center">
                  <div className="text-down font-mono font-bold">{fmt(sentimentData.aaii.bearish, 1)}%</div>
                  <div className="text-muted-foreground">Bearish</div>
                </div>
              </div>
              </div>
              <div className="border-t border-border pt-2 flex justify-between items-center">
                <div onClick={() => openDetail('sentiment', 'naaim')} className="rounded p-1 cursor-pointer hover:bg-accent transition-colors" role="button" tabIndex={0}>
                  <div className="text-[10px] text-muted-foreground flex items-center gap-1">NAAIM Exposure <ChevronRight size={11}/></div>
                  <div className="text-sm font-mono font-bold text-foreground">{fmt(sentimentData.naaim.value, 1)}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-muted-foreground">Put/Call Ratio</div>
                  <div className="text-sm font-mono font-bold text-foreground">{fmt(sentimentData.putcall.value, 2)}</div>
                  {sentimentData.putcall.connected === false && <div className="text-[8px] text-muted-foreground">Not in database</div>}
                </div>
              </div>
            </div>
          </div>

          {/* News */}
          <div className="bg-card border border-border rounded p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Newspaper size={12} className="text-primary" />
              <span className="text-xs font-bold text-foreground">Latest News Feed</span>
            </div>
            <div className="space-y-2">
              {newsFeed.map(n => (
                <div key={n.id} className="border-b border-border pb-1.5 last:border-0 last:pb-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-[10px] font-mono text-muted-foreground">{n.time}</span>
                    <span className="text-[10px] bg-secondary text-muted-foreground px-1 rounded">{n.source}</span>
                    <span className={`text-[10px] px-1 rounded ${
                      n.sentiment === 'positive' ? 'bg-green-100 text-up dark:bg-green-950/30' :
                      n.sentiment === 'negative' ? 'bg-red-100 text-down dark:bg-red-950/30' :
                      'bg-secondary text-muted-foreground'
                    }`}>{n.tag}</span>
                  </div>
                  <p className="text-xs text-foreground leading-tight">{n.title}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
