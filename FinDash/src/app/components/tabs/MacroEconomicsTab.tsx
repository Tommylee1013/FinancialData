import React, { useState } from "react";
import { MacroWorldMap } from "../WorldMap";
import { MiniLineChart } from "../CandlestickChart";
import { TimeSeriesChart } from "../TimeSeriesChart";
import { macroCalendar, macroVariables, countryMacroData, countryMarkers } from "../../data/mockData";
import { TrendingUp, TrendingDown } from "lucide-react";
import { openDetail } from "../../detailNavigation";

const fmt = (v: number | null | undefined, d = 2) => v == null ? '—' : v.toFixed(d);

function CountryIndicatorSections() {
  const [countryFilter, setCountryFilter] = useState('ALL');
  const macroCountries = Array.from(new Map((macroVariables as any[]).map(item => [item.country || 'Global', {
    key: item.country || 'Global', name: item.countryName || item.country || 'Global', flag: item.flag || '🌐',
    ids: (macroVariables as any[]).filter(candidate => (candidate.country || 'Global') === (item.country || 'Global')).map(candidate => candidate.id),
  }])).values());
  const activeCountry = macroCountries.find(country => country.key === countryFilter);
  const items = activeCountry ? macroVariables.filter(item => activeCountry.ids.includes(item.id)) : macroVariables;
  return <section className="space-y-3">
    <div className="flex items-center gap-2 flex-wrap">
      {[{ key: 'ALL', name: 'All Countries', flag: '🌐' }, ...macroCountries].map(country => <button key={country.key} onClick={() => setCountryFilter(country.key)} className={`text-xs px-3 py-1.5 rounded transition-colors ${countryFilter === country.key ? 'bg-primary text-white' : 'bg-card border border-border text-muted-foreground hover:text-foreground'}`}>{country.flag} {country.name}</button>)}
    </div>
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="px-4 py-3 bg-secondary/60 border-b border-border flex items-center justify-between">
        <div><h2 className="text-sm font-bold">Macro Indicator Board</h2><p className="text-[10px] text-muted-foreground mt-0.5">{activeCountry ? `${activeCountry.flag} ${activeCountry.name}` : 'Global coverage'} · Click an indicator for full research view</p></div>
        <span className="text-[10px] font-mono text-muted-foreground">{items.length} SERIES</span>
      </div>
      <div className={`grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-px bg-border ${countryFilter === 'ALL' ? 'max-h-[620px] overflow-y-auto' : ''}`}>
        {items.map(item => {
          const country = macroCountries.find(entry => entry.ids.includes(item.id));
          const beat = item.value >= item.forecast;
          const rising = item.value >= item.prev;
          return <button key={item.id} onClick={() => openDetail('macro', item.id)} className="text-left bg-card p-3 hover:bg-accent transition-colors group">
            <div className="flex items-start justify-between gap-2"><div><div className="text-[9px] text-muted-foreground mb-0.5">{country?.flag} {country?.key}</div><div className="text-xs font-bold group-hover:text-primary">{item.name}</div><div className="text-[9px] text-muted-foreground mt-0.5 line-clamp-1">{item.desc}</div></div><span className={`text-[9px] px-1.5 py-0.5 rounded ${beat ? 'bg-green-100 text-up dark:bg-green-950/30' : 'bg-red-100 text-down dark:bg-red-950/30'}`}>{beat ? 'BEAT' : 'MISS'}</span></div>
            <div className="flex items-end justify-between mt-3"><div><div className="text-xl font-mono font-bold">{fmt(item.value)}{item.unit}</div><div className={`text-[10px] font-mono ${rising ? 'text-up' : 'text-down'}`}>{rising ? '▲' : '▼'} Prev {fmt(item.prev)}{item.unit}</div></div><MiniLineChart data={item.trend.slice(-30)} width={86} height={34} color={rising ? '#16A34A' : '#DC2626'} fill={false}/></div>
            <div className="flex justify-between mt-2 pt-2 border-t border-border text-[9px] text-muted-foreground"><span>Forecast {fmt(item.forecast)}{item.unit}</span><span>{item.period}</span></div>
          </button>;
        })}
      </div>
    </div>
  </section>;
}

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
      <div className="max-h-[443px] overflow-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0 z-10 bg-secondary">
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
                  <td className={`px-3 py-2 font-mono font-bold ${beat ? 'text-up' : 'text-down'}`}>{fmt(row.actual)}</td>
                  <td className="px-3 py-2 font-mono text-muted-foreground">{fmt(row.forecast)}</td>
                  <td className="px-3 py-2 font-mono text-muted-foreground">{fmt(row.prev)}</td>
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
              <span className="w-14 text-right font-mono font-semibold text-foreground">{val.toFixed(2)}%</span>
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
  const data = mv.trend.map((d) => ({ period: d.date, value: parseFloat(d.v.toFixed(2)) }));

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
          <div className="text-base font-mono font-bold text-foreground">{fmt(mv.value)}{mv.unit}</div>
          <div className="flex gap-3 text-[10px] font-mono">
            <span className="text-muted-foreground">Forecast <span className="text-foreground">{fmt(mv.forecast)}{mv.unit}</span></span>
            <span className="text-muted-foreground">Prev <span className="text-foreground">{fmt(mv.prev)}{mv.unit}</span></span>
          </div>
        </div>
      </div>
      <div className="flex justify-end mb-2"><button onClick={() => openDetail('macro', mv.id)} className="text-[10px] font-semibold text-primary hover:underline">Research details →</button></div>
      <TimeSeriesChart key={selected} data={data} height={220} digits={2}/>
    </div>
  );
}

export function MacroEconomicsTab() {
  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
      <CountryIndicatorSections />
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
