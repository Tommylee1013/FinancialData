import React, { useMemo, useState } from "react";
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { FreightWorldMap } from "../WorldMap";
import { freightIndices, portMarkers } from "../../data/mockData";
import { TrendingUp, TrendingDown, Search, MapPin } from "lucide-react";
import { openDetail } from "../../detailNavigation";
import { paddedDomain } from "../../chartUtils";

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
      <button onClick={(event) => { event.stopPropagation(); openDetail('freight', fi.id); }} className="mt-2 text-[10px] font-semibold text-primary hover:underline">
        Research details →
      </button>
    </div>
  );
}

function FreightLineChart({ selected }: { selected: string }) {
  const idx = freightIndices.find(f => f.id === selected) ?? freightIndices[0];
  const data = idx.trend.map((d) => ({
    period: d.date,
    [idx.name]: Math.round(d.v),
  }));
  const domain = paddedDomain(data.map(point => point[idx.name]));

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
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="freightGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="period" tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} minTickGap={28} tickFormatter={v => String(v).slice(2, 10)} />
          <YAxis domain={domain} tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} tickFormatter={fmt} width={55} />
          <Tooltip content={<CustomTooltip />} />
          <Area key={`freight-area-${idx.id}`} type="monotone" dataKey={idx.name} name={idx.name} stroke="var(--primary)" fill="url(#freightGrad)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function AllFreightChart({ items }: { items: typeof freightIndices }) {
  const compared = items.slice(0, 6);
  const len = compared[0]?.trend.length ?? 0;
  const data = Array.from({ length: len }, (_, i) => {
    const point: Record<string, any> = { period: compared[0]?.trend[i]?.date };
    compared.forEach(fi => {
      point[fi.name] = Math.round(fi.trend[i]?.v ?? 0);
    });
    return point;
  });

  const colors = ['var(--primary)', 'var(--up)', 'var(--down)', '#F59E0B', '#8B5CF6', '#06B6D4'];
  const domain = paddedDomain(data.flatMap(point => compared.map(fi => point[fi.name])));

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="mb-3"><h3 className="text-sm font-bold text-foreground">Selected Group Comparison</h3><p className="text-[10px] text-muted-foreground mt-0.5">First {compared.length} indicators in the current filter</p></div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="period" tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} minTickGap={28} tickFormatter={v => String(v).slice(2, 10)} />
          <YAxis domain={domain} tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} width={50} tickFormatter={fmt} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          {compared.map((fi, i) => (
            <Line key={`all-freight-${fi.id}`} type="monotone" dataKey={fi.name} name={fi.name} stroke={colors[i % colors.length]} strokeWidth={1.5} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SupplyChainTab() {
  const [selected, setSelected] = useState(freightIndices[0].id);
  const [groupFilter, setGroupFilter] = useState('All');
  const [releaseFilter, setReleaseFilter] = useState('All');
  const [countryFilter, setCountryFilter] = useState('All');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 24;

  const rows = freightIndices as Array<(typeof freightIndices)[0] & { symbol?: string; category?: string; subCategory?: string; country?: string; countryName?: string; flag?: string; unit?: string }>;
  const groups = useMemo(() => ['All', ...Array.from(new Set(rows.map(item => item.category || 'Other'))).sort()], [rows]);
  const releases = useMemo(() => ['All', ...Array.from(new Set(rows.filter(item => groupFilter === 'All' || (item.category || 'Other') === groupFilter).map(item => item.subCategory || 'General'))).sort()], [rows, groupFilter]);
  const countries = useMemo(() => ['All', ...Array.from(new Set(rows.map(item => item.countryName || item.country || 'Global'))).sort()], [rows]);
  const filtered = useMemo(() => rows.filter(item => {
    const search = query.trim().toLowerCase();
    return (groupFilter === 'All' || (item.category || 'Other') === groupFilter)
      && (releaseFilter === 'All' || (item.subCategory || 'General') === releaseFilter)
      && (countryFilter === 'All' || (item.countryName || item.country || 'Global') === countryFilter)
      && (!search || `${item.name} ${item.symbol || ''} ${item.desc || ''}`.toLowerCase().includes(search));
  }), [rows, groupFilter, releaseFilter, countryFilter, query]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const visible = filtered.slice(page * pageSize, (page + 1) * pageSize);
  const chartItems = filtered.length ? filtered : rows.slice(0, 6);
  const mapCountryAliases: Record<string, string> = { 'United States': 'USA', 'United Kingdom': 'UK' };
  const mapCountry = mapCountryAliases[countryFilter] || countryFilter;
  const mapMarkers = countryFilter === 'All' ? portMarkers : portMarkers.filter(marker => marker.country === mapCountry);

  const resetPage = () => setPage(0);

  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      <section className="bg-card border border-border rounded overflow-hidden">
        <div className="p-4 border-b border-border bg-secondary/40">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div><h2 className="text-sm font-bold">Supply Chain Indicator Library</h2><p className="text-[10px] text-muted-foreground mt-1">Organized by release group and reporting country · {rows.length} live series</p></div>
            <label className="flex items-center gap-2 bg-background border border-border rounded px-3 py-2 min-w-60"><Search size={13} className="text-muted-foreground"/><input value={query} onChange={event => { setQuery(event.target.value); resetPage(); }} placeholder="Search symbol or indicator…" className="w-full bg-transparent text-xs outline-none"/></label>
          </div>
          <div className="mt-4 space-y-3">
            <div className="flex items-start gap-3"><span className="w-24 shrink-0 pt-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">Release group</span><div className="flex flex-wrap gap-1.5">{groups.map(group => <button key={group} onClick={() => { setGroupFilter(group); setReleaseFilter('All'); resetPage(); }} className={`px-2.5 py-1 rounded text-[10px] border ${groupFilter === group ? 'bg-primary border-primary text-white' : 'border-border text-muted-foreground hover:text-foreground'}`}>{group}</button>)}</div></div>
            <div className="flex items-start gap-3"><span className="w-24 shrink-0 pt-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">Indicator type</span><div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto">{releases.map(release => <button key={release} onClick={() => { setReleaseFilter(release); resetPage(); }} className={`px-2.5 py-1 rounded text-[10px] border ${releaseFilter === release ? 'bg-accent border-primary text-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>{release}</button>)}</div></div>
            <div className="flex items-start gap-3"><span className="w-24 shrink-0 pt-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">Country</span><div className="flex flex-wrap gap-1.5">{countries.map(country => <button key={country} onClick={() => { setCountryFilter(country); resetPage(); }} className={`px-2.5 py-1 rounded text-[10px] border ${countryFilter === country ? 'bg-accent border-primary text-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>{country}</button>)}</div></div>
          </div>
        </div>
        <div className="px-4 py-2 border-b border-border flex items-center justify-between text-[10px] text-muted-foreground"><span>{filtered.length} matching series · page {page + 1} of {pageCount}</span><span>{groupFilter} / {releaseFilter} / {countryFilter}</span></div>
        <div className="grid gap-2 p-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))' }}>
        {visible.map(fi => (
          <div key={fi.id} onClick={() => setSelected(fi.id)} className="cursor-pointer">
            <div className={`rounded transition-all ${selected === fi.id ? 'ring-2 ring-primary' : ''}`}>
              <FreightIndexCard fi={fi} />
            </div>
          </div>
        ))}
        {!visible.length && <div className="col-span-full py-12 text-center text-xs text-muted-foreground">No indicators match the selected filters.</div>}
        </div>
        {pageCount > 1 && <div className="px-4 py-3 border-t border-border flex justify-center gap-2"><button disabled={page === 0} onClick={() => setPage(value => Math.max(0, value - 1))} className="px-3 py-1.5 rounded border border-border text-xs disabled:opacity-30">Previous</button><button disabled={page >= pageCount - 1} onClick={() => setPage(value => Math.min(pageCount - 1, value + 1))} className="px-3 py-1.5 rounded border border-border text-xs disabled:opacity-30">Next</button></div>}
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Selected freight chart */}
        <FreightLineChart selected={selected} />
        {/* All comparison chart */}
        <AllFreightChart items={chartItems as typeof freightIndices} />
      </div>

      {/* World Map */}
      <div className="bg-card border border-border rounded overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2"><MapPin size={15} className="text-primary"/><div><h2 className="text-sm font-bold text-foreground">Global Logistics Monitor</h2><p className="text-[10px] text-muted-foreground mt-0.5">Major port benchmarks and regional freight pressure</p></div></div>
          <div className="flex gap-3 text-[10px] text-muted-foreground"><span><b className="text-foreground">{mapMarkers.length}</b> hubs</span><span><b className="text-up">{mapMarkers.filter(marker => marker.change >= 0).length}</b> rising</span><span><b className="text-down">{mapMarkers.filter(marker => marker.change < 0).length}</b> falling</span></div>
        </div>
        <FreightWorldMap markers={mapMarkers} />
      </div>

      {/* Port data table */}
      <div className="bg-card border border-border rounded overflow-hidden">
        <div className="px-3 py-2 bg-secondary border-b border-border">
          <span className="text-xs font-bold text-foreground">Port Freight Index Details</span>
        </div>
        <div className="max-h-[443px] overflow-auto">
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-10 bg-secondary">
              <tr>
                {['Port', 'Country', 'Index', 'Value', 'Change%', 'Prev', 'As of'].map(h => (
                  <th key={h} className="text-left px-3 py-2 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {mapMarkers.map(p => {
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
