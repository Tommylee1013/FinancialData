import React, { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  AreaChart, Area, BarChart, Bar
} from "recharts";
import { yieldCurveUS, yieldCurveKR, krSwapRates, moneyMarket, generateTrend } from "../../data/mockData";

const fmt = (v: number, d = 2) => v.toFixed(d);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-card border border-border rounded p-2 text-xs shadow-lg">
      <div className="font-semibold text-foreground mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color }} className="font-mono">
          {p.name}: {p.value?.toFixed(2)}%
        </div>
      ))}
    </div>
  );
};

function YieldCurveChart() {
  const combinedData = yieldCurveUS.map((d, i) => ({
    tenor: d.tenor,
    'US Current': d.yield,
    'US Prev': d.prev,
    'KR Current': yieldCurveKR[i]?.yield,
    'KR Prev': yieldCurveKR[i]?.prev,
  }));

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-foreground">Yield Curve</h3>
        <div className="flex gap-3 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-primary inline-block" /> US</span>
          <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-up inline-block" /> KR</span>
          <span className="flex items-center gap-1"><span className="w-4 h-0.5 border-t border-dashed border-muted-foreground inline-block" /> Prev Day</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={combinedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="tenor" tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} />
          <YAxis tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} domain={['auto', 'auto']} tickFormatter={v => `${v}%`} />
          <Tooltip content={<CustomTooltip />} />
          <Line key="us-cur" type="monotone" dataKey="US Current" name="US Current" stroke="var(--primary)" strokeWidth={2} dot={false} />
          <Line key="us-prev" type="monotone" dataKey="US Prev" name="US Prev" stroke="var(--primary)" strokeWidth={1} strokeDasharray="4 2" dot={false} opacity={0.5} />
          <Line key="kr-cur" type="monotone" dataKey="KR Current" name="KR Current" stroke="var(--up)" strokeWidth={2} dot={false} />
          <Line key="kr-prev" type="monotone" dataKey="KR Prev" name="KR Prev" stroke="var(--up)" strokeWidth={1} strokeDasharray="4 2" dot={false} opacity={0.5} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function Spread10Y2Y() {
  const usSpread = yieldCurveUS.find(d => d.tenor === '10Y')!.yield - yieldCurveUS.find(d => d.tenor === '2Y')!.yield;
  const krSpread = yieldCurveKR.find(d => d.tenor === '10Y')!.yield - yieldCurveKR.find(d => d.tenor === '2Y')!.yield;
  const spreadTrend = generateTrend(usSpread, 60, 0.08, 0.02);
  const data = spreadTrend.map((d, i) => ({ t: i, v: d.v - usSpread + usSpread }));

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-foreground">10Y-2Y Spread</h3>
      </div>
      <div className="flex gap-6 mb-3">
        <div>
          <div className="text-[10px] text-muted-foreground">🇺🇸 US 10Y-2Y</div>
          <div className={`text-lg font-mono font-bold ${usSpread >= 0 ? 'text-up' : 'text-down'}`}>{usSpread >= 0 ? '+' : ''}{fmt(usSpread * 100, 1)}bp</div>
        </div>
        <div>
          <div className="text-[10px] text-muted-foreground">🇰🇷 KR 10Y-2Y</div>
          <div className={`text-lg font-mono font-bold ${krSpread >= 0 ? 'text-up' : 'text-down'}`}>{krSpread >= 0 ? '+' : ''}{fmt(krSpread * 100, 1)}bp</div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={100}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis hide />
          <YAxis hide domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 11 }} />
          <Area key="spread-area" type="monotone" dataKey="v" name="10Y-2Y Spread" stroke="var(--primary)" fill="url(#sg)" strokeWidth={1.5} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function YieldTable({ title, data }: { title: string; data: typeof yieldCurveUS }) {
  return (
    <div className="bg-card border border-border rounded overflow-hidden">
      <div className="px-3 py-2 bg-secondary border-b border-border">
        <span className="text-xs font-bold text-foreground">{title}</span>
      </div>
      <table className="w-full text-xs">
        <thead className="bg-secondary/50">
          <tr>
            {['Tenor', 'Yield(%)', 'Prev(%)', 'Change(bp)'].map(h => (
              <th key={h} className="text-left px-3 py-1.5 text-muted-foreground font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map(row => {
            const chg = (row.yield - row.prev) * 100;
            const up = chg >= 0;
            return (
              <tr key={row.tenor} className="border-t border-border hover:bg-secondary/50">
                <td className="px-3 py-1.5 font-semibold text-foreground">{row.tenor}</td>
                <td className="px-3 py-1.5 font-mono text-foreground">{fmt(row.yield)}%</td>
                <td className="px-3 py-1.5 font-mono text-muted-foreground">{fmt(row.prev)}%</td>
                <td className={`px-3 py-1.5 font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
                  {up ? '+' : ''}{fmt(chg, 1)}bp
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function SwapRateTable() {
  return (
    <div className="bg-card border border-border rounded overflow-hidden">
      <div className="px-3 py-2 bg-secondary border-b border-border">
        <span className="text-xs font-bold text-foreground">🇰🇷 Korea IRS / CRS Rates</span>
        <span className="ml-2 text-[10px] text-muted-foreground">IRS: Interest Rate Swap · CRS: Cross-Currency Swap</span>
      </div>
      <table className="w-full text-xs">
        <thead className="bg-secondary/50">
          <tr>
            {['Tenor', 'IRS(%)', 'IRS Δ(bp)', 'CRS(%)', 'CRS Δ(bp)', 'IRS-CRS Spread(bp)'].map(h => (
              <th key={h} className="text-left px-3 py-1.5 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {krSwapRates.map(row => {
            const irsUp = row.irsChange >= 0;
            const crsUp = row.crsChange >= 0;
            const spread = (row.irs - row.crs) * 100;
            return (
              <tr key={row.tenor} className="border-t border-border hover:bg-secondary/50">
                <td className="px-3 py-1.5 font-semibold text-foreground">{row.tenor}</td>
                <td className="px-3 py-1.5 font-mono text-foreground">{fmt(row.irs)}%</td>
                <td className={`px-3 py-1.5 font-mono font-semibold ${irsUp ? 'text-up' : 'text-down'}`}>
                  {irsUp ? '+' : ''}{fmt(row.irsChange * 100, 1)}bp
                </td>
                <td className="px-3 py-1.5 font-mono text-foreground">{fmt(row.crs)}%</td>
                <td className={`px-3 py-1.5 font-mono font-semibold ${crsUp ? 'text-up' : 'text-down'}`}>
                  {crsUp ? '+' : ''}{fmt(row.crsChange * 100, 1)}bp
                </td>
                <td className="px-3 py-1.5 font-mono text-primary font-semibold">{fmt(spread, 1)}bp</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function MoneyMarketPanel() {
  return (
    <div className="bg-card border border-border rounded overflow-hidden">
      <div className="px-3 py-2 bg-secondary border-b border-border">
        <span className="text-xs font-bold text-foreground">Short-term Rates · Money Market</span>
      </div>
      <table className="w-full text-xs">
        <thead className="bg-secondary/50">
          <tr>
            {['Name', 'Rate(%)', 'Day Change'].map(h => (
              <th key={h} className="text-left px-3 py-1.5 text-muted-foreground font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {moneyMarket.map(row => {
            const up = row.change >= 0;
            return (
              <tr key={row.name} className="border-t border-border hover:bg-secondary/50">
                <td className="px-3 py-1.5 text-foreground whitespace-nowrap">
                  <span className="mr-1.5">{row.flag}</span>{row.name}
                </td>
                <td className="px-3 py-1.5 font-mono font-semibold text-foreground">{row.value.toFixed(2)}%</td>
                <td className={`px-3 py-1.5 font-mono font-semibold ${up ? 'text-up' : row.change === 0 ? 'text-muted-foreground' : 'text-down'}`}>
                  {up ? '+' : ''}{row.change.toFixed(2)}%
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function FixedIncomeTab() {
  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 space-y-4">
          <YieldCurveChart />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <YieldTable title="🇺🇸 US Treasury Yields" data={yieldCurveUS} />
            <YieldTable title="🇰🇷 Korea Gov Bond Yields" data={yieldCurveKR} />
          </div>
          <SwapRateTable />
        </div>
        <div className="space-y-4">
          <Spread10Y2Y />
          <MoneyMarketPanel />
        </div>
      </div>
    </div>
  );
}
