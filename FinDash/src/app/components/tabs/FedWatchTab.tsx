import React, { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, CalendarDays, Database, Gauge, RefreshCw } from "lucide-react";
import { TimeSeriesChart } from "../TimeSeriesChart";
import { paddedDomain } from "../../chartUtils";

type Scenario = { scenarioBp: number; probability: number };
type Meeting = { meetingDate: string; asOf: string; contract: string; impliedRate: number; effectiveRate: number; scenarios: Scenario[] };
type Payload = { meetings: Meeting[]; selectedMeeting: Meeting | null; scenarios: Scenario[]; series: any[]; futures: any[]; updatedAt?: string };

const colors = ['#1D4ED8','#2563EB','#3B82F6','#60A5FA','#64748B','#F59E0B','#F97316','#EF4444','#B91C1C'];
const scenarioLabel = (bp: number) => bp === 0 ? 'No Change' : `${bp > 0 ? '+' : ''}${bp} bp`;

export function FedWatchTab() {
  const [data, setData] = useState<Payload | null>(null);
  const [meeting, setMeeting] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = async (value = meeting) => {
    setLoading(true); setError('');
    try {
      const response = await fetch(`/api/fedwatch${value ? `?meeting=${encodeURIComponent(value)}` : ''}`);
      const body = await response.json(); if (!response.ok) throw new Error(body.error || `API ${response.status}`);
      setData(body); if (!value && body.selectedMeeting) setMeeting(String(body.selectedMeeting.meetingDate));
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(''); }, []);

  const aggregate = useMemo(() => {
    const scenarios = data?.scenarios || [];
    return {
      cut: scenarios.filter(item => item.scenarioBp < 0).reduce((sum, item) => sum + item.probability, 0) * 100,
      hold: scenarios.filter(item => item.scenarioBp === 0).reduce((sum, item) => sum + item.probability, 0) * 100,
      hike: scenarios.filter(item => item.scenarioBp > 0).reduce((sum, item) => sum + item.probability, 0) * 100,
    };
  }, [data]);
  const activeScenarios = (data?.scenarios || []).filter(item => item.probability > 0.0001);
  const rateDomain = paddedDomain((data?.series || []).flatMap(row => [row.impliedRate, row.effectiveRate]), 0.08);

  if (loading && !data) return <div className="p-12 text-center text-sm text-muted-foreground">Loading Fed funds futures model…</div>;
  return <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">
    <div className="bg-card border border-border rounded p-4 flex flex-wrap items-center gap-3">
      <div className="mr-auto"><div className="flex items-center gap-2"><Gauge size={17} className="text-primary"/><h2 className="text-base font-bold">Fed Policy Probability Monitor</h2></div><p className="text-[10px] text-muted-foreground mt-1">FedWatch-style estimate from CBOT 30-Day Fed Funds Futures and EFFR</p></div>
      <button onClick={() => load()} className="flex items-center gap-1.5 px-3 py-2 rounded border border-border text-xs hover:bg-secondary"><RefreshCw size={12} className={loading ? 'animate-spin' : ''}/>Refresh</button>
    </div>
    {error && <div className="p-3 rounded border border-down/30 bg-down/5 text-down text-xs">{error}</div>}
    {!data?.meetings.length ? <div className="bg-card border border-border rounded p-12 text-center"><Database className="mx-auto text-muted-foreground mb-3"/><div className="font-semibold">No modeled meetings in DuckDB</div><div className="text-xs text-muted-foreground mt-2">Run the fed_policy job to populate probabilities.</div></div> : <>
      <div className="bg-card border border-border rounded p-2 flex gap-2 overflow-x-auto">
        {data.meetings.map(item => <button key={item.meetingDate} onClick={() => { setMeeting(String(item.meetingDate)); load(String(item.meetingDate)); }} className={`shrink-0 rounded px-3 py-2 text-left border ${String(item.meetingDate) === meeting ? 'bg-primary text-primary-foreground border-primary' : 'border-border hover:bg-secondary'}`}><div className="text-[9px] opacity-70">FOMC DECISION</div><div className="text-xs font-mono font-bold mt-0.5">{String(item.meetingDate)}</div><div className="text-[9px] opacity-70 mt-0.5">{item.contract}</div></button>)}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {[['Rate Cut',aggregate.cut,'text-primary','#2563EB'],['No Change',aggregate.hold,'text-foreground','#64748B'],['Rate Hike',aggregate.hike,'text-down','#DC2626']].map(([label,value,tone,color]) => <div key={String(label)} className="bg-card border border-border rounded p-4"><div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div><div className={`text-3xl font-mono font-bold mt-2 ${tone}`}>{Number(value).toFixed(1)}%</div><div className="h-1.5 bg-secondary rounded mt-3 overflow-hidden"><div className="h-full rounded" style={{width:`${value}%`,background:String(color)}}/></div></div>)}
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 bg-card border border-border rounded p-4">
          <div className="flex justify-between mb-4"><div><h3 className="text-sm font-bold">Target Rate Probability</h3><p className="text-[10px] text-muted-foreground mt-1">Latest distribution for {String(data.selectedMeeting?.meetingDate)}</p></div><div className="text-right text-[10px] text-muted-foreground"><div>As of {String(data.selectedMeeting?.asOf)}</div><div className="font-mono mt-1">{data.selectedMeeting?.contract}</div></div></div>
          <div className="space-y-3">{activeScenarios.map((item,index) => <div key={item.scenarioBp} className="grid grid-cols-[90px_1fr_70px] items-center gap-3"><span className="text-xs font-mono font-semibold">{scenarioLabel(item.scenarioBp)}</span><div className="h-7 bg-secondary rounded overflow-hidden"><div className="h-full rounded flex items-center px-2" style={{width:`${Math.max(2,item.probability*100)}%`,background:colors[index%colors.length]}}/></div><span className="text-right text-sm font-mono font-bold">{(item.probability*100).toFixed(1)}%</span></div>)}</div>
        </div>
        <div className="bg-card border border-border rounded p-4">
          <h3 className="text-sm font-bold mb-3">Market Pricing</h3>
          <div className="space-y-3">{[['Futures-implied rate',data.selectedMeeting?.impliedRate],['Effective fed funds rate',data.selectedMeeting?.effectiveRate],['Implied difference',(data.selectedMeeting?.impliedRate ?? 0)-(data.selectedMeeting?.effectiveRate ?? 0)]].map(([label,value]) => <div key={String(label)} className="bg-secondary rounded p-3"><div className="text-[10px] text-muted-foreground">{label}</div><div className="text-lg font-mono font-bold mt-1">{Number(value).toFixed(3)}%</div></div>)}</div>
          <div className="mt-3 pt-3 border-t border-border flex items-center gap-2 text-[10px] text-muted-foreground"><CalendarDays size={12}/>Meeting date: {String(data.selectedMeeting?.meetingDate)}</div>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded p-4"><div className="mb-3"><h3 className="text-sm font-bold">Probability History</h3><p className="text-[10px] text-muted-foreground mt-1">Complete probability history · {data.series.length.toLocaleString()} observations</p></div><ResponsiveContainer width="100%" height={300}><AreaChart data={data.series}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/><XAxis dataKey="date" minTickGap={35} tick={{fontSize:9,fill:'var(--muted-foreground)'}}/><YAxis domain={[0,100]} tickFormatter={v=>`${v}%`} tick={{fontSize:9,fill:'var(--muted-foreground)'}}/><Tooltip contentStyle={{background:'var(--card)',border:'1px solid var(--border)',fontSize:10}}/><Legend wrapperStyle={{fontSize:10}}/>{data.scenarios.map((scenario,index)=><Area key={scenario.scenarioBp} type="monotone" stackId="prob" dataKey={`p${scenario.scenarioBp}`} name={scenarioLabel(scenario.scenarioBp)} stroke={colors[index%colors.length]} fill={colors[index%colors.length]} fillOpacity={0.7}/>)}</AreaChart></ResponsiveContainer></div>
        <div className="bg-card border border-border rounded p-4"><div className="mb-3"><h3 className="text-sm font-bold">Implied Rate vs EFFR</h3><p className="text-[10px] text-muted-foreground mt-1">Futures-implied monthly average against the effective policy rate</p></div><ResponsiveContainer width="100%" height={300}><LineChart data={data.series}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/><XAxis dataKey="date" minTickGap={35} tick={{fontSize:9,fill:'var(--muted-foreground)'}}/><YAxis domain={rateDomain} tickFormatter={v=>`${Number(v).toFixed(2)}%`} tick={{fontSize:9,fill:'var(--muted-foreground)'}}/><Tooltip contentStyle={{background:'var(--card)',border:'1px solid var(--border)',fontSize:10}}/><Legend wrapperStyle={{fontSize:10}}/><Line type="monotone" dataKey="impliedRate" name="Implied Rate" stroke="var(--primary)" strokeWidth={2} dot={false}/><Line type="stepAfter" dataKey="effectiveRate" name="EFFR" stroke="var(--foreground)" strokeWidth={1.5} dot={false}/></LineChart></ResponsiveContainer></div>
      </div>
      <div className="bg-card border border-border rounded p-4"><div className="flex items-center gap-2 mb-3"><Activity size={14} className="text-primary"/><div><h3 className="text-sm font-bold">{data.selectedMeeting?.contract} Futures</h3><p className="text-[10px] text-muted-foreground">Full OHLC history · Scroll to zoom</p></div></div><TimeSeriesChart data={data.futures} height={420} initialMode="candle" initialMonths={6}/></div>
    </>}
  </div>;
}
