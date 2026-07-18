import React, { useState } from "react";
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { FreightWorldMap } from "../WorldMap";
import { freightIndices, portMarkers } from "../../data/mockData";
import { TrendingUp, TrendingDown } from "lucide-react";

const fmt = (v: number) => v.toLocaleString('en-US');

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-card border border-border rounded p-2 text-xs shadow-lg">
      <div className="font-semibold text-foreground mb-1">Period {label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color }} className="font-mono">{p.name}: {fmt(p.value)}</div>
      ))}
    </div>
  );
};

function FreightIndexCard({ fi }: { fi: typeof freightIndices[0] }) {
  const up = fi.change >= 0;
  return (
    <div className="bg-card border border-border rounded p-3">
      <div className="flex justify-between items-start mb-1">
        <div>
          <div className="text-xs font-bold text-foreground">{fi.name}</div>
          <div className="text-[10px] text-muted-foreground">{fi.desc}</div>
        </div>
        <span className={`flex items-center gap-0.5 text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${up ? 'text-up bg-green-50 dark:bg-green-950/30' : 'text-down bg-red-50 dark:bg-red-950/30'}`}>
          {up ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
          {up ? '+' : ''}{fi.changePct.toFixed(2)}%
        </span>
      </div>
      <div className="text-lg font-mono font-bold text-foreground">{fmt(fi.value)}</div>
      <div className={`text-xs font-mono ${up ? 'text-up' : 'text-down'}`}>
        {up ? '+' : ''}{fmt(fi.change)} pts
      </div>
    </div>
  );
}

function FreightLineChart({ selected }: { selected: string }) {
  const idx = freightIndices.find(f => f.id === selected) ?? freightIndices[0];
  const data = idx.trend.map((d, i) => ({
    period: i,
    [idx.name]: Math.round(d.v),
  }));

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-bold text-foreground">{idx.fullName}</h3>
          <div className="text-[10px] text-muted-foreground">{idx.desc} · Last 90 Days</div>
        </div>
        <div className="text-right">
          <div className="text-base font-mono font-bold text-foreground">{fmt(idx.value)}</div>
          <div className={`text-xs font-mono ${idx.change >= 0 ? 'text-up' : 'text-down'}`}>
            {idx.change >= 0 ? '+' : ''}{fmt(idx.change)} ({idx.changePct >= 0 ? '+' : ''}{idx.changePct.toFixed(2)}%)
          </div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="freightGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="period" hide />
          <YAxis tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} tickFormatter={fmt} width={55} />
          <Tooltip content={<CustomTooltip />} />
          <Area key={`freight-area-${idx.id}`} type="monotone" dataKey={idx.name} name={idx.name} stroke="var(--primary)" fill="url(#freightGrad)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function AllFreightChart() {
  const len = freightIndices[0].trend.length;
  const data = Array.from({ length: len }, (_, i) => {
    const point: Record<string, any> = { period: i };
    freightIndices.forEach(fi => {
      point[fi.name] = Math.round(fi.trend[i]?.v ?? 0);
    });
    return point;
  });

  const colors = ['var(--primary)', 'var(--up)', 'var(--down)', '#F59E0B', '#8B5CF6', '#06B6D4'];

  return (
    <div className="bg-card border border-border rounded p-4">
      <h3 className="text-sm font-bold text-foreground mb-3">Major Freight Index Comparison</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="period" hide />
          <YAxis tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} width={50} tickFormatter={fmt} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          {freightIndices.map((fi, i) => (
            <Line key={`all-freight-${fi.id}`} type="monotone" dataKey={fi.name} name={fi.name} stroke={colors[i % colors.length]} strokeWidth={1.5} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SupplyChainTab() {
  const [selected, setSelected] = useState(freightIndices[0].id);

  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      {/* Freight Index Cards */}
      <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))' }}>
        {freightIndices.map(fi => (
          <div key={fi.id} onClick={() => setSelected(fi.id)} className="cursor-pointer">
            <div className={`rounded transition-all ${selected === fi.id ? 'ring-2 ring-primary' : ''}`}>
              <FreightIndexCard fi={fi} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Selected freight chart */}
        <FreightLineChart selected={selected} />
        {/* All comparison chart */}
        <AllFreightChart />
      </div>

      {/* World Map */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-0.5 h-4 bg-primary rounded-full" />
          <h2 className="text-sm font-bold text-foreground" style={{ fontFamily: 'Roboto Condensed, sans-serif' }}>Global Port Freight Index Status</h2>
          <span className="text-xs text-muted-foreground">· Click markers for details</span>
        </div>
        <FreightWorldMap markers={portMarkers} />
      </div>

      {/* Port data table */}
      <div className="bg-card border border-border rounded overflow-hidden">
        <div className="px-3 py-2 bg-secondary border-b border-border">
          <span className="text-xs font-bold text-foreground">Port Freight Index Details</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-secondary/50">
              <tr>
                {['Port', 'Country', 'Index', 'Value', 'Change%', 'Prev', 'As of'].map(h => (
                  <th key={h} className="text-left px-3 py-2 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {portMarkers.map(p => {
                const up = p.change >= 0;
                return (
                  <tr key={p.id} className="border-t border-border hover:bg-secondary/50">
                    <td className="px-3 py-2 font-semibold text-foreground">{p.city}</td>
                    <td className="px-3 py-2 text-muted-foreground">{p.country}</td>
                    <td className="px-3 py-2 text-primary font-medium">{p.index}</td>
                    <td className="px-3 py-2 font-mono font-semibold text-foreground">{p.value.toLocaleString()} {p.unit}</td>
                    <td className={`px-3 py-2 font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
                      {up ? '+' : ''}{p.change.toFixed(2)}%
                    </td>
                    <td className="px-3 py-2 font-mono text-muted-foreground">{p.prev.toLocaleString()}</td>
                    <td className="px-3 py-2 font-mono text-muted-foreground">{p.date}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
