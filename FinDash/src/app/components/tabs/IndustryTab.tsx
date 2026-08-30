import React, { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { MiniLineChart } from "../CandlestickChart";
import { industryData } from "../../data/mockData";
import { TrendingUp, TrendingDown, Search } from "lucide-react";
import { openDetail } from "../../detailNavigation";
import { paddedDomain } from "../../chartUtils";

const fmt = (v: number, d = 2) => v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });

const categoryColors: Record<string, string> = {
  'Semiconductors': '#8B5CF6',
  'Energy & Fuel': '#F59E0B',
  'Real Estate': '#06B6D4',
  'Materials': '#EC4899',
  'Steel & Metals': '#64748B',
};

function CategoryBadge({ category }: { category: string }) {
  const color = categoryColors[category] ?? '#6B7280';
  return (
    <span
      className="px-1.5 py-0.5 rounded text-[10px] font-medium text-white"
      style={{ background: color }}
    >
      {category}
    </span>
  );
}

function IndustryBoardRow({ item, isSelected, onClick }: { item: typeof industryData[0]; isSelected: boolean; onClick: () => void }) {
  const up = item.changePct >= 0;
  return (
    <tr
      onClick={onClick}
      className={`border-t border-border cursor-pointer transition-colors text-xs ${isSelected ? 'bg-accent' : 'hover:bg-secondary'}`}
    >
      <td className="px-3 py-2"><CategoryBadge category={item.category} /></td>
      <td className="px-3 py-2 font-semibold text-foreground whitespace-nowrap">{item.name}</td>
      <td className="px-3 py-2 text-muted-foreground text-[10px]">{item.unit}</td>
      <td className="px-3 py-2 font-mono font-bold text-foreground">{fmt(item.value)}</td>
      <td className={`px-3 py-2 font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
        {up ? '+' : ''}{fmt(item.change)}
      </td>
      <td className={`px-3 py-2 font-mono font-bold ${up ? 'text-up' : 'text-down'}`}>
        <span className="flex items-center gap-0.5">
          {up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
          {up ? '+' : ''}{fmt(item.changePct)}%
        </span>
      </td>
      <td className="px-3 py-2 font-mono text-muted-foreground">{fmt(item.high)}</td>
      <td className="px-3 py-2 font-mono text-muted-foreground">{fmt(item.low)}</td>
      <td className="px-3 py-2">
        <MiniLineChart data={item.trend} width={70} height={24} color={up ? '#16A34A' : '#DC2626'} fill={false} />
      </td>
    </tr>
  );
}

function DetailPanel({ item }: { item: typeof industryData[0] }) {
  const up = item.changePct >= 0;
  const chartData = item.trend.map((d) => ({ t: d.date, v: parseFloat(d.v.toFixed(2)) }));
  const domain = paddedDomain(chartData.map(point => point.v));
  const catColor = categoryColors[item.category] ?? '#6B7280';

  return (
    <div className="bg-card border border-border rounded p-4 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <CategoryBadge category={item.category} />
          <h2 className="text-sm font-bold text-foreground mt-1">{item.name}</h2>
          <div className="text-xs text-muted-foreground">{item.unit}</div>
        </div>
        <div className="text-right">
          <div className="text-xl font-mono font-bold text-foreground">{fmt(item.value)}</div>
          <div className={`text-xs font-mono font-semibold flex items-center gap-1 justify-end ${up ? 'text-up' : 'text-down'}`}>
            {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {up ? '+' : ''}{fmt(item.change)} ({up ? '+' : ''}{fmt(item.changePct)}%)
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-secondary rounded p-2">
          <div className="text-[10px] text-muted-foreground">Daily High</div>
          <div className="text-sm font-mono font-semibold text-foreground">{fmt(item.high)}</div>
        </div>
        <div className="bg-secondary rounded p-2">
          <div className="text-[10px] text-muted-foreground">Daily Low</div>
          <div className="text-sm font-mono font-semibold text-foreground">{fmt(item.low)}</div>
        </div>
      </div>

      <div>
        <div className="text-xs font-semibold text-muted-foreground mb-1.5">30-Day Price History</div>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="indGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={up ? '#16A34A' : '#DC2626'} stopOpacity={0.25} />
                <stop offset="95%" stopColor={up ? '#16A34A' : '#DC2626'} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} minTickGap={28} tickFormatter={v => String(v).slice(2, 10)} />
            <YAxis domain={domain} tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} width={62} tickFormatter={v => Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })} />
            <Tooltip
              contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 11 }}
              formatter={(v: any) => [v.toLocaleString(), item.name]}
            />
            <Area key={`ind-area-${item.id}`} type="monotone" dataKey="v" name={item.name} stroke={up ? '#16A34A' : '#DC2626'} fill="url(#indGrad)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <button onClick={() => openDetail('industry', item.id)} className="w-full rounded bg-primary text-primary-foreground py-2 text-xs font-semibold hover:opacity-90">
        Open professional research view →
      </button>
    </div>
  );
}

function CategorySummary() {
  const cats = [...new Set(industryData.map(d => d.category))];
  return (
    <div className="bg-card border border-border rounded p-3">
      <div className="text-xs font-bold text-foreground mb-2">Category Overview</div>
      <div className="space-y-2">
        {cats.map(cat => {
          const items = industryData.filter(d => d.category === cat);
          const avgPct = items.reduce((s, i) => s + i.changePct, 0) / items.length;
          const up = avgPct >= 0;
          const color = categoryColors[cat] ?? '#6B7280';
          return (
            <div key={cat} className="flex items-center gap-2 text-[11px]">
              <div className="w-2 h-2 rounded-sm shrink-0" style={{ background: color }} />
              <span className="flex-1 text-muted-foreground">{cat}</span>
              <span className="text-muted-foreground">{items.length}</span>
              <span className={`w-16 text-right font-mono font-semibold ${up ? 'text-up' : 'text-down'}`}>
                {up ? '+' : ''}{avgPct.toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function IndustryOverview() {
  const sorted = [...industryData].sort((a, b) => b.changePct - a.changePct);
  const advancing = industryData.filter(item => item.changePct >= 0).length;
  const average = industryData.reduce((sum, item) => sum + item.changePct, 0) / industryData.length;
  return <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
    {[{ label: 'Breadth', value: `${advancing} / ${industryData.length}`, note: 'Advancing indicators', tone: advancing >= industryData.length / 2 ? 'text-up' : 'text-down' }, { label: 'Average Change', value: `${average >= 0 ? '+' : ''}${fmt(average)}%`, note: 'Across all industries', tone: average >= 0 ? 'text-up' : 'text-down' }, { label: 'Momentum Leader', value: sorted[0].name, note: `+${fmt(sorted[0].changePct)}%`, tone: 'text-up' }, { label: 'Largest Drag', value: sorted.at(-1)!.name, note: `${fmt(sorted.at(-1)!.changePct)}%`, tone: 'text-down' }].map(stat => <div key={stat.label} className="bg-card border border-border rounded p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">{stat.label}</div><div className={`text-sm font-semibold mt-1 truncate ${stat.tone}`}>{stat.value}</div><div className="text-[10px] text-muted-foreground mt-0.5">{stat.note}</div></div>)}
  </div>;
}

function IndustryHeatmap() {
  return <div className="bg-card border border-border rounded p-4"><div className="flex justify-between items-end mb-3"><div><h3 className="text-sm font-bold">Industry Momentum Map</h3><p className="text-[10px] text-muted-foreground mt-0.5">Size represents relative move · color represents direction</p></div><span className="text-[10px] text-muted-foreground">DAILY CHANGE</span></div><div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-2">{industryData.map(item => { const intensity = Math.min(0.92, 0.18 + Math.abs(item.changePct) / 4); return <button key={item.id} onClick={() => openDetail('industry', item.id)} className="rounded p-3 text-left min-h-20 transition-transform hover:scale-[1.02]" style={{ background: item.changePct >= 0 ? `rgba(22,163,74,${intensity})` : `rgba(220,38,38,${intensity})`, color: intensity > .5 ? 'white' : 'var(--foreground)' }}><div className="text-[9px] opacity-75 truncate">{item.category}</div><div className="text-xs font-semibold mt-1 line-clamp-2">{item.name}</div><div className="text-sm font-mono font-bold mt-2">{item.changePct >= 0 ? '+' : ''}{fmt(item.changePct)}%</div></button>; })}</div></div>;
}

const allCategories = ['All', ...new Set(industryData.map(d => d.category))];

export function IndustryTab() {
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(industryData[0]);

  const filtered = industryData.filter(d =>
    (filter === 'All' || d.category === filter) &&
    d.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center bg-card border border-border rounded px-2 gap-1">
          <Search size={12} className="text-muted-foreground" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search indices..."
            className="text-xs py-1.5 bg-transparent outline-none text-foreground placeholder:text-muted-foreground w-28"
          />
        </div>
        {allCategories.map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`text-xs px-3 py-1.5 rounded transition-colors ${filter === cat ? 'bg-primary text-white' : 'bg-card border border-border text-muted-foreground hover:text-foreground'}`}
          >
            {cat}
          </button>
        ))}
      </div>

      <IndustryOverview />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 space-y-3">
          <div className="bg-card border border-border rounded overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-secondary">
                  <tr>
                    {['Category', 'Index', 'Unit', 'Price', 'Change', 'Change%', 'High', 'Low', 'Trend'].map(h => (
                      <th key={h} className="text-left px-3 py-2 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(item => (
                    <IndustryBoardRow
                      key={item.id}
                      item={item}
                      isSelected={selected.id === item.id}
                      onClick={() => setSelected(item)}
                    />
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={9} className="px-3 py-8 text-center text-muted-foreground text-xs">No results found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <DetailPanel item={selected} />
          <CategorySummary />
        </div>
      </div>
      <IndustryHeatmap />
    </div>
  );
}
