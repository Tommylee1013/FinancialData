import React, { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { MiniLineChart } from "../CandlestickChart";
import { commodities } from "../../data/mockData";
import { TrendingUp, TrendingDown, Search } from "lucide-react";

const fmt = (v: number, d = 2) => v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

const categories = ['All', 'Energy', 'Precious Metals', 'Base Metals', 'Industrial'];

function BoardRow({ c, isSelected, onClick }: { c: typeof commodities[0]; isSelected: boolean; onClick: () => void }) {
  const up = c.changePct >= 0;
  return (
    <tr
      onClick={onClick}
      className={`border-t border-border cursor-pointer transition-colors text-xs ${isSelected ? 'bg-accent' : 'hover:bg-secondary'}`}
    >
      <td className="px-3 py-2">
        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium bg-secondary text-muted-foreground`}>{c.category}</span>
      </td>
      <td className="px-3 py-2 font-semibold text-foreground">{c.name}</td>
      <td className="px-3 py-2 font-mono text-muted-foreground text-[10px]">{c.unit}</td>
      <td className="px-3 py-2 font-mono font-bold text-foreground">{fmt(c.value)}</td>
      <td className={`px-3 py-2 font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
        {up ? '+' : ''}{fmt(c.change)}
      </td>
      <td className={`px-3 py-2 font-mono font-bold ${up ? 'text-up' : 'text-down'}`}>
        <span className="flex items-center gap-0.5">
          {up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
          {up ? '+' : ''}{fmt(c.changePct)}%
        </span>
      </td>
      <td className="px-3 py-2 font-mono text-muted-foreground">{fmt(c.high)}</td>
      <td className="px-3 py-2 font-mono text-muted-foreground">{fmt(c.low)}</td>
      <td className="px-3 py-2">
        <MiniLineChart data={c.trend} width={70} height={24} color={up ? '#16A34A' : '#DC2626'} fill={false} />
      </td>
    </tr>
  );
}

function DetailPanel({ c }: { c: typeof commodities[0] }) {
  const up = c.changePct >= 0;
  const chartData = c.trend.map((d, i) => ({ t: i, v: parseFloat(d.v.toFixed(2)) }));

  return (
    <div className="bg-card border border-border rounded p-4 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-bold text-foreground">{c.name}</h2>
          <div className="text-xs text-muted-foreground">{c.category} · {c.unit}</div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-mono font-bold text-foreground">{fmt(c.value)}</div>
          <div className={`text-sm font-mono font-semibold flex items-center gap-1 justify-end ${up ? 'text-up' : 'text-down'}`}>
            {up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {up ? '+' : ''}{fmt(c.change)} ({up ? '+' : ''}{fmt(c.changePct)}%)
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {[
          { label: 'Daily High', value: fmt(c.high) },
          { label: 'Daily Low', value: fmt(c.low) },
        ].map(item => (
          <div key={item.label} className="bg-secondary rounded p-2">
            <div className="text-[10px] text-muted-foreground">{item.label}</div>
            <div className="text-sm font-mono font-semibold text-foreground">{item.value}</div>
          </div>
        ))}
      </div>

      <div>
        <div className="text-xs font-semibold text-muted-foreground mb-1.5">30-Day Price History</div>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="commGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={up ? '#16A34A' : '#DC2626'} stopOpacity={0.25} />
                <stop offset="95%" stopColor={up ? '#16A34A' : '#DC2626'} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="t" hide />
            <YAxis tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} width={55} tickFormatter={v => v.toLocaleString()} />
            <Tooltip
              contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 11 }}
              formatter={(v: any) => [v.toLocaleString(), c.name]}
            />
            <Area key={`comm-area-${c.id}`} type="monotone" dataKey="v" name={c.name} stroke={up ? '#16A34A' : '#DC2626'} fill="url(#commGrad)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[10px] text-muted-foreground bg-secondary rounded p-2">
        ※ Will be replaced with live TradingView candlestick chart upon integration
      </div>
    </div>
  );
}

export function CommoditiesTab() {
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(commodities[0]);

  const filtered = commodities.filter(c =>
    (filter === 'All' || c.category === filter) &&
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center bg-card border border-border rounded px-2 gap-1">
          <Search size={12} className="text-muted-foreground" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search commodities..."
            className="text-xs py-1.5 bg-transparent outline-none text-foreground placeholder:text-muted-foreground w-32"
          />
        </div>
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`text-xs px-3 py-1.5 rounded transition-colors ${filter === cat ? 'bg-primary text-white' : 'bg-card border border-border text-muted-foreground hover:text-foreground'}`}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <div className="bg-card border border-border rounded overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-secondary">
                  <tr>
                    {['Category', 'Commodity', 'Unit', 'Price', 'Change', 'Change%', 'High', 'Low', 'Trend'].map(h => (
                      <th key={h} className="text-left px-3 py-2 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(c => (
                    <BoardRow key={c.id} c={c} isSelected={selected.id === c.id} onClick={() => setSelected(c)} />
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={9} className="px-3 py-8 text-center text-muted-foreground text-xs">No results found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div>
          <DetailPanel c={selected} />
        </div>
      </div>
    </div>
  );
}
