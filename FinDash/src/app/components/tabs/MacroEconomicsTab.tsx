import React, { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { MacroWorldMap } from "../WorldMap";
import { macroCalendar, macroVariables, countryMacroData, countryMarkers } from "../../data/mockData";
import { TrendingUp, TrendingDown } from "lucide-react";

const fmt = (v: number, d = 1) => v.toFixed(d);

function MacroTable() {
  const [sortKey, setSortKey] = useState<string>('country');
  const rows = macroCalendar;

  return (
    <div className="bg-card border border-border rounded overflow-hidden">
      <div className="px-3 py-2 bg-secondary border-b border-border flex items-center justify-between">
        <span className="text-xs font-bold text-foreground">Economic Indicator Releases</span>
        <div className="flex gap-2 text-[10px]">
          <span className="px-1.5 py-0.5 rounded bg-red-100 text-down dark:bg-red-950/30 font-medium">● High Impact</span>
          <span className="px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-600 dark:bg-yellow-950/30 font-medium">● Medium Impact</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-secondary/50">
            <tr>
              {['Country', 'Indicator', 'Actual', 'Forecast', 'Previous', 'Period', 'Result'].map(h => (
                <th key={h} className="text-left px-3 py-2 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const beat = row.actual >= row.forecast;
              const up = row.actual >= row.prev;
              return (
                <tr key={i} className="border-t border-border hover:bg-secondary/50">
                  <td className="px-3 py-2">{row.country}</td>
                  <td className="px-3 py-2 font-semibold text-foreground whitespace-nowrap">{row.event}</td>
                  <td className={`px-3 py-2 font-mono font-bold ${beat ? 'text-up' : 'text-down'}`}>{row.actual}</td>
                  <td className="px-3 py-2 font-mono text-muted-foreground">{row.forecast}</td>
                  <td className="px-3 py-2 font-mono text-muted-foreground">{row.prev}</td>
                  <td className="px-3 py-2 text-muted-foreground">{row.period}</td>
                  <td className="px-3 py-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${beat ? 'bg-green-100 text-up dark:bg-green-950/30' : 'bg-red-100 text-down dark:bg-red-950/30'}`}>
                      {beat ? 'Beat' : 'Miss'}
                    </span>
                    {row.importance === 'high' && <span className="ml-1 text-down">●</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CountryComparePanel() {
  const countries = Object.values(countryMacroData);
  const [metric, setMetric] = useState<'cpi' | 'gdp' | 'unemploy' | 'rate'>('cpi');
  const metricLabels = { cpi: 'CPI YoY', gdp: 'GDP QoQ', unemploy: 'Unemployment', rate: 'Policy Rate' };
  const sorted = [...countries].sort((a, b) => b[metric] - a[metric]);

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-foreground">Country Comparison</h3>
        <div className="flex gap-1">
          {(Object.keys(metricLabels) as Array<keyof typeof metricLabels>).map(k => (
            <button
              key={k}
              onClick={() => setMetric(k)}
              className={`text-[10px] px-2 py-0.5 rounded transition-colors ${metric === k ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
            >
              {metricLabels[k]}
            </button>
          ))}
        </div>
      </div>
      <div className="space-y-1.5">
        {sorted.map(c => {
          const val = c[metric];
          const maxVal = Math.max(...countries.map(cc => cc[metric]));
          const barW = (val / maxVal) * 100;
          const color = metric === 'cpi' ? (val > 3 ? '#DC2626' : val > 2 ? '#F59E0B' : '#16A34A') :
                        metric === 'gdp' ? (val > 4 ? '#16A34A' : val > 1 ? '#3B82F6' : '#F59E0B') :
                        metric === 'unemploy' ? (val < 4 ? '#16A34A' : val < 7 ? '#F59E0B' : '#DC2626') :
                        '#3B82F6';
          return (
            <div key={c.iso} className="flex items-center gap-2 text-[11px]">
              <span className="w-16 text-muted-foreground flex items-center gap-1">
                <span>{c.flag}</span><span className="truncate">{c.name}</span>
              </span>
              <div className="flex-1 h-4 bg-secondary rounded-sm overflow-hidden">
                <div
                  className="h-full rounded-sm transition-all"
                  style={{ width: `${barW}%`, background: color, opacity: 0.85 }}
                />
              </div>
              <span className="w-12 text-right font-mono font-semibold text-foreground">{val.toFixed(1)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MacroTrendCharts() {
  const [selected, setSelected] = useState(macroVariables[0].id);
  const mv = macroVariables.find(m => m.id === selected) ?? macroVariables[0];
  const data = mv.trend.map((d, i) => ({ period: i, value: parseFloat(d.v.toFixed(2)) }));

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1">
        {macroVariables.map(m => (
          <button
            key={m.id}
            onClick={() => setSelected(m.id)}
            className={`text-[10px] px-2 py-1 rounded whitespace-nowrap transition-colors ${selected === m.id ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
          >
            {m.name}
          </button>
        ))}
      </div>
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-sm font-bold text-foreground">{mv.name} — {mv.desc}</h3>
          <div className="text-[10px] text-muted-foreground">{mv.period} · Monthly Trend (24 months)</div>
        </div>
        <div className="text-right">
          <div className="text-base font-mono font-bold text-foreground">{mv.value}{mv.unit}</div>
          <div className="flex gap-3 text-[10px] font-mono">
            <span className="text-muted-foreground">Forecast <span className="text-foreground">{mv.forecast}{mv.unit}</span></span>
            <span className="text-muted-foreground">Prev <span className="text-foreground">{mv.prev}{mv.unit}</span></span>
          </div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="macroGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.25} />
              <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="period" hide />
          <YAxis tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} width={40} tickFormatter={v => `${v}%`} />
          <Tooltip
            contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 11 }}
            formatter={(v: any) => [`${v}%`, mv.name]}
          />
          <Area key={`macro-area-${selected}`} type="monotone" dataKey="value" name={mv.name} stroke="var(--primary)" fill="url(#macroGrad)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MacroEconomicsTab() {
  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 space-y-4">
          <MacroTable />
          <MacroTrendCharts />
        </div>
        <div className="space-y-4">
          <CountryComparePanel />
        </div>
      </div>

      {/* World Map */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-0.5 h-4 bg-primary rounded-full" />
          <h2 className="text-sm font-bold text-foreground" style={{ fontFamily: 'Roboto Condensed, sans-serif' }}>Global Macro Overview Map</h2>
          <span className="text-xs text-muted-foreground">· Click markers for country details</span>
        </div>
        <MacroWorldMap markers={countryMarkers} countryData={countryMacroData} />
      </div>
    </div>
  );
}
