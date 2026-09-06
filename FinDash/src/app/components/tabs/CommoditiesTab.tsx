import React, { useState } from "react";
import { MiniLineChart } from "../CandlestickChart";
import { TimeSeriesChart } from "../TimeSeriesChart";
import { commodities } from "../../data/mockData";
import { TrendingUp, TrendingDown, Search } from "lucide-react";
import { openDetail } from "../../detailNavigation";

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
  const chartData = c.trend.map((d) => ({ t: d.date, v: parseFloat(d.v.toFixed(2)) }));

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
        <div className="text-xs font-semibold text-muted-foreground mb-1.5">Complete Price History</div>
        <TimeSeriesChart key={c.id} data={(c as any).ohlc?.length ? (c as any).ohlc : chartData} height={210} color={up ? '#16A34A' : '#DC2626'} digits={2}/>
      </div>

      <button onClick={() => openDetail('commodity', c.id)} className="w-full rounded bg-primary text-primary-foreground py-2 text-xs font-semibold hover:opacity-90">
        Open professional research view →
      </button>
    </div>
  );
}

function CommodityOverview() {
  const sorted = [...commodities].sort((a, b) => b.changePct - a.changePct);
  const up = commodities.filter(item => item.changePct >= 0).length;
  const avg = commodities.reduce((sum, item) => sum + item.changePct, 0) / commodities.length;
  const stats = [
    { label: 'Market Breadth', value: `${up} / ${commodities.length}`, note: 'Advancing contracts', color: up >= commodities.length / 2 ? 'text-up' : 'text-down' },
    { label: 'Average Move', value: `${avg >= 0 ? '+' : ''}${fmt(avg)}%`, note: 'Equal-weight basket', color: avg >= 0 ? 'text-up' : 'text-down' },
    { label: 'Top Performer', value: sorted[0].name, note: `+${fmt(sorted[0].changePct)}%`, color: 'text-up' },
    { label: 'Weakest', value: sorted.at(-1)!.name, note: `${fmt(sorted.at(-1)!.changePct)}%`, color: 'text-down' },
  ];
  return <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">{stats.map(stat => <div key={stat.label} className="bg-card border border-border rounded p-3"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">{stat.label}</div><div className={`text-sm font-semibold mt-1 truncate ${stat.color}`}>{stat.value}</div><div className="text-[10px] text-muted-foreground mt-0.5">{stat.note}</div></div>)}</div>;
}

function CommodityCategoryPulse() {
  const cats = categories.slice(1).map(category => {
    const items = commodities.filter(item => item.category === category);
    const avg = items.length ? items.reduce((sum, item) => sum + item.changePct, 0) / items.length : 0;
    return { category, items, avg };
  }).filter(group => group.items.length);
  return <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
    <div className="bg-card border border-border rounded p-4"><h3 className="text-sm font-bold">Category Pulse</h3><p className="text-[10px] text-muted-foreground mt-0.5 mb-3">Equal-weight daily performance by commodity group</p><div className="space-y-3">{cats.map(group => <div key={group.category}><div className="flex justify-between text-[11px] mb-1"><span className="font-medium">{group.category}</span><span className={`font-mono font-semibold ${group.avg >= 0 ? 'text-up' : 'text-down'}`}>{group.avg >= 0 ? '+' : ''}{fmt(group.avg)}%</span></div><div className="h-2 bg-secondary rounded overflow-hidden"><div className="h-full rounded" style={{ width: `${Math.min(100, 25 + Math.abs(group.avg) * 20)}%`, background: group.avg >= 0 ? '#16A34A' : '#DC2626' }}/></div></div>)}</div></div>
    <div className="bg-card border border-border rounded p-4"><h3 className="text-sm font-bold">Cross-Commodity Signals</h3><p className="text-[10px] text-muted-foreground mt-0.5 mb-3">Quick read from current price action</p><div className="grid grid-cols-2 gap-2">{commodities.slice().sort((a,b) => Math.abs(b.changePct)-Math.abs(a.changePct)).slice(0,6).map(item => <button key={item.id} onClick={() => openDetail('commodity', item.id)} className="text-left bg-secondary/60 hover:bg-accent rounded p-2"><div className="text-[10px] text-muted-foreground">{item.category}</div><div className="text-xs font-semibold truncate mt-0.5">{item.name}</div><div className={`text-xs font-mono mt-1 ${item.changePct >= 0 ? 'text-up' : 'text-down'}`}>{item.changePct >= 0 ? '+' : ''}{fmt(item.changePct)}%</div></button>)}</div></div>
  </div>;
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

      <CommodityOverview />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <div className="bg-card border border-border rounded overflow-hidden">
            <div className="max-h-[443px] overflow-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 z-10 bg-secondary">
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
      <CommodityCategoryPulse />
    </div>
  );
}
