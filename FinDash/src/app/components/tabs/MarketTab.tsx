import React, { useState } from "react";
import { TrendingUp, TrendingDown, Newspaper } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { MiniLineChart, CandlestickChart } from "../CandlestickChart";
import {
  marketIndices, volatilityIndices, sectorData, krSectorData,
  newsFeed, sentimentData, generateOHLC
} from "../../data/mockData";

const fmt = (v: number, d = 2) => v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

function FngGauge({ value, label }: { value: number; label: string }) {
  const pct = value / 100;
  const color = value < 25 ? '#DC2626' : value < 45 ? '#F97316' : value < 55 ? '#EAB308' : value < 75 ? '#84CC16' : '#16A34A';
  const angle = -90 + pct * 180;
  const cx = 60, cy = 60, r = 46;
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
    <div className="flex flex-col items-center">
      <svg width={120} height={72}>
        <path d={arcPath(-180, 0)} fill="none" stroke="var(--muted)" strokeWidth={10} />
        <path d={arcPath(-180, startAngle + pct * 180)} fill="none" stroke={color} strokeWidth={10} />
        <line x1={cx} y1={cy} x2={needleX} y2={needleY} stroke="var(--foreground)" strokeWidth={2} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={3} fill="var(--foreground)" />
        <text x={cx} y={cy + 18} textAnchor="middle" fontSize={16} fontWeight={700} fontFamily="JetBrains Mono" fill={color}>{value}</text>
      </svg>
      <span className="text-xs font-semibold mt-1" style={{ color }}>{label}</span>
      <span className="text-[10px] text-muted-foreground">CNN Fear & Greed</span>
    </div>
  );
}

export function MarketTab() {
  const [selectedIdx, setSelectedIdx] = useState(marketIndices[0]);
  const ohlcData = generateOHLC(selectedIdx.value * 0.92, 60, selectedIdx.value * 0.01);

  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
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
                  {marketIndices.map(idx => {
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
                TradingView integration pending · Simulated data
              </div>
            </div>
            <div className="overflow-x-auto">
              <CandlestickChart data={ohlcData} width={680} height={200} showAxes />
            </div>
          </div>

          {/* Sectors */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-card border border-border rounded p-3">
              <div className="text-xs font-bold text-foreground mb-2">🇺🇸 S&P 500 Sector Performance</div>
              <div className="space-y-1">
                {sectorData.map(s => {
                  const up = s.changePct >= 0;
                  const barW = Math.abs(s.changePct) / 2 * 100;
                  return (
                    <div key={s.name} className="flex items-center gap-2 text-[11px]">
                      <span className="w-28 text-muted-foreground truncate">{s.name}</span>
                      <div className="flex-1 flex items-center gap-1">
                        <div className="flex-1 h-3 bg-secondary rounded-sm overflow-hidden">
                          <div
                            className="h-full rounded-sm"
                            style={{ width: `${Math.min(barW, 100)}%`, background: up ? '#16A34A' : '#DC2626', opacity: 0.8 }}
                          />
                        </div>
                        <span className={`w-14 text-right font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
                          {up ? '+' : ''}{fmt(s.changePct)}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-card border border-border rounded p-3">
              <div className="text-xs font-bold text-foreground mb-2">🇰🇷 KOSPI Sector Performance</div>
              <div className="space-y-1">
                {krSectorData.map(s => {
                  const up = s.changePct >= 0;
                  const barW = Math.abs(s.changePct) / 2.5 * 100;
                  return (
                    <div key={s.name} className="flex items-center gap-2 text-[11px]">
                      <span className="w-20 text-muted-foreground">{s.name}</span>
                      <div className="flex-1 flex items-center gap-1">
                        <div className="flex-1 h-3 bg-secondary rounded-sm overflow-hidden">
                          <div
                            className="h-full rounded-sm"
                            style={{ width: `${Math.min(barW, 100)}%`, background: up ? '#16A34A' : '#DC2626', opacity: 0.8 }}
                          />
                        </div>
                        <span className={`w-14 text-right font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
                          {up ? '+' : ''}{fmt(s.changePct)}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
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
                  <div key={v.id} className="flex items-center justify-between py-1 border-b border-border last:border-0">
                    <div>
                      <div className="text-xs font-semibold text-foreground">{v.name}</div>
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
            <div className="flex justify-center mb-3">
              <FngGauge value={sentimentData.fng.value} label={sentimentData.fng.label} />
            </div>
            <div className="space-y-2 border-t border-border pt-2">
              <div className="text-[10px] font-semibold text-muted-foreground mb-1">AAII Sentiment Survey</div>
              <div className="flex gap-2 text-[11px]">
                <div className="flex-1 text-center">
                  <div className="text-up font-mono font-bold">{sentimentData.aaii.bullish}%</div>
                  <div className="text-muted-foreground">Bullish</div>
                </div>
                <div className="flex-1 text-center">
                  <div className="text-muted-foreground font-mono font-bold">{sentimentData.aaii.neutral}%</div>
                  <div className="text-muted-foreground">Neutral</div>
                </div>
                <div className="flex-1 text-center">
                  <div className="text-down font-mono font-bold">{sentimentData.aaii.bearish}%</div>
                  <div className="text-muted-foreground">Bearish</div>
                </div>
              </div>
              <div className="border-t border-border pt-2 flex justify-between items-center">
                <div>
                  <div className="text-[10px] text-muted-foreground">NAAIM Exposure</div>
                  <div className="text-sm font-mono font-bold text-foreground">{sentimentData.naaim.value}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-muted-foreground">Put/Call Ratio</div>
                  <div className="text-sm font-mono font-bold text-foreground">{sentimentData.putcall.value}</div>
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
