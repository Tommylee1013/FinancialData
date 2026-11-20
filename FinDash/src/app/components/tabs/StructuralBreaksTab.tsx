import { useMemo, useState } from 'react';
import { Activity, AlertTriangle, BrainCircuit, CheckCircle2, Gauge, Play, RefreshCw, Waves } from 'lucide-react';

type MarketModel = {
  asset: string; symbol: string; price: string; change: string;
  regime: string; confidence: number; summary: string;
  probabilities: { label: string; value: number; color: string; note: string }[];
};

const markets: MarketModel[] = [
  { asset: 'S&P 500', symbol: 'SPX', price: '7,561.67', change: '-0.40%', regime: 'Trend Expansion', confidence: 68, summary: 'The index remains in an upward trend, but bubble-test pressure and momentum dispersion are rising.', probabilities: [
    { label: 'Bull / Expansion', value: 68, color: '#2563EB', note: 'Persistent positive drift' },
    { label: 'Sideways', value: 17, color: '#64748B', note: 'Mean-reverting range' },
    { label: 'Bear / Contraction', value: 10, color: '#DC2626', note: 'Negative growth regime' },
    { label: 'Stress / Break', value: 5, color: '#F59E0B', note: 'Discontinuous transition' },
  ]},
  { asset: 'KOSPI', symbol: 'KOSPI', price: '5,290.53', change: '-0.98%', regime: 'Late Expansion', confidence: 57, summary: 'Trend remains constructive while foreign-flow reversal and volatility suggest a transition risk.', probabilities: [
    { label: 'Bull / Expansion', value: 57, color: '#2563EB', note: 'Positive medium-term trend' },
    { label: 'Sideways', value: 22, color: '#64748B', note: 'Increasing consolidation risk' },
    { label: 'Bear / Contraction', value: 13, color: '#DC2626', note: 'Downside state probability' },
    { label: 'Stress / Break', value: 8, color: '#F59E0B', note: 'Transition risk elevated' },
  ]},
  { asset: 'NASDAQ 100', symbol: 'NDX', price: '25,136.27', change: '-0.91%', regime: 'Bubble Watch', confidence: 61, summary: 'Explosive-root tests are elevated even though the dominant trend state remains positive.', probabilities: [
    { label: 'Bull / Expansion', value: 54, color: '#2563EB', note: 'Strong price persistence' },
    { label: 'Sideways', value: 14, color: '#64748B', note: 'Low range probability' },
    { label: 'Bear / Contraction', value: 9, color: '#DC2626', note: 'Limited contraction signal' },
    { label: 'Stress / Break', value: 23, color: '#F59E0B', note: 'SADF warning active' },
  ]},
  { asset: 'MSCI World', symbol: 'MXWO', price: '1,115.55', change: '-1.51%', regime: 'Risk-Off Transition', confidence: 64, summary: 'Cross-market breadth and volatility features point to a possible transition from expansion.', probabilities: [
    { label: 'Bull / Expansion', value: 29, color: '#2563EB', note: 'Trend state weakening' },
    { label: 'Sideways', value: 24, color: '#64748B', note: 'Range state possible' },
    { label: 'Bear / Contraction', value: 32, color: '#DC2626', note: 'Downside state rising' },
    { label: 'Stress / Break', value: 15, color: '#F59E0B', note: 'Break probability elevated' },
  ]},
];

const modelRows = [
  { model: 'Gaussian HMM', family: 'Latent state', signal: 'Expansion', probability: 74, status: 'Stable', description: '4-state model on return and volatility features' },
  { model: 'Markov Switching', family: 'Time series', signal: 'High-growth / low-vol', probability: 69, status: 'Stable', description: 'Regime-dependent mean and variance' },
  { model: 'SADF / GSADF', family: 'Statistical test', signal: 'Mild exuberance', probability: 38, status: 'Watch', description: 'Right-tailed explosive-root monitoring' },
  { model: 'Technical ML', family: 'Gradient boosting', signal: 'Risk-on', probability: 66, status: 'Stable', description: 'MA, RSI, breadth, volume and volatility features' },
  { model: 'Change Point', family: 'Bayesian / PELT', signal: 'No recent break', probability: 21, status: 'Stable', description: 'Mean and variance shift detection' },
];

const features = [
  ['200D trend distance', 82, 'Positive'], ['Market breadth', 63, 'Positive'], ['Volatility term structure', 58, 'Neutral'],
  ['Credit spread impulse', 44, 'Neutral'], ['RSI divergence', 31, 'Negative'], ['SADF statistic', 27, 'Negative'],
];

function RegimeChart({ seed }: { seed: number }) {
  const values = useMemo(() => Array.from({ length: 100 }, (_, i) => 100 + i * .42 + Math.sin((i + seed) / 6) * 3.8 + Math.sin((i + seed) / 17) * 6), [seed]);
  const min = Math.min(...values), max = Math.max(...values);
  const points = values.map((value, i) => `${(i / 99) * 900},${190 - ((value - min) / (max - min)) * 150}`).join(' ');
  return <div className="relative h-[250px] w-full overflow-hidden rounded-md border border-border bg-background">
    <svg viewBox="0 0 900 220" preserveAspectRatio="none" className="h-full w-full">
      <rect x="0" y="0" width="238" height="220" fill="#2563EB" opacity=".05"/>
      <rect x="238" y="0" width="126" height="220" fill="#F59E0B" opacity=".08"/>
      <rect x="364" y="0" width="313" height="220" fill="#2563EB" opacity=".05"/>
      <rect x="677" y="0" width="61" height="220" fill="#DC2626" opacity=".08"/>
      <rect x="738" y="0" width="162" height="220" fill="#2563EB" opacity=".05"/>
      {[45,95,145,195].map(y => <line key={y} x1="0" y1={y} x2="900" y2={y} stroke="currentColor" opacity=".08"/>) }
      <polyline points={points} fill="none" stroke="#2563EB" strokeWidth="2.2" vectorEffect="non-scaling-stroke"/>
      <line x1="738" y1="0" x2="738" y2="220" stroke="#DC2626" strokeDasharray="4 4" opacity=".7"/>
    </svg>
    <div className="absolute bottom-2 left-3 flex flex-wrap gap-3 text-[11px] text-muted-foreground"><span><i className="mr-1 inline-block h-2 w-2 bg-blue-500/30"/>Expansion</span><span><i className="mr-1 inline-block h-2 w-2 bg-amber-500/30"/>Transition</span><span><i className="mr-1 inline-block h-2 w-2 bg-red-500/30"/>Stress</span></div>
  </div>;
}

export function StructuralBreaksTab() {
  const [marketIndex, setMarketIndex] = useState(0);
  const [horizon, setHorizon] = useState('5Y');
  const [running, setRunning] = useState(false);
  const [updated, setUpdated] = useState('Nov 21, 2026 · 15:30 KST');
  const market = markets[marketIndex];

  const runDiagnostic = () => {
    setRunning(true);
    window.setTimeout(() => { setRunning(false); setUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' · sample rerun'); }, 700);
  };

  return <div className="mx-auto max-w-screen-2xl space-y-4 p-4 sm:p-6">
    <section className="rounded-lg border border-border bg-card shadow-sm">
      <div className="flex flex-col gap-4 border-b border-border p-4 lg:flex-row lg:items-center">
        <div className="flex-1"><div className="flex items-center gap-2"><BrainCircuit size={19} className="text-primary"/><h2 className="text-lg font-semibold">Structural Break &amp; Regime Diagnostics</h2></div><p className="mt-1 text-xs text-muted-foreground">Multi-model inference across latent states, explosive-root tests and technical ML signals</p></div>
        <div className="flex flex-wrap gap-2">
          <select value={marketIndex} onChange={event => setMarketIndex(Number(event.target.value))} className="h-9 rounded-md border border-border bg-background px-3 text-sm font-medium outline-none focus:border-primary">{markets.map((item,index) => <option key={item.symbol} value={index}>{item.asset} · {item.symbol}</option>)}</select>
          <div className="flex rounded-md border border-border bg-background p-0.5">{['1Y','3Y','5Y','10Y'].map(item => <button key={item} onClick={() => setHorizon(item)} className={`rounded px-2.5 py-1 text-xs font-semibold ${horizon === item ? 'bg-primary text-primary-foreground':'text-muted-foreground hover:bg-secondary'}`}>{item}</button>)}</div>
          <button onClick={runDiagnostic} disabled={running} className="flex h-9 items-center gap-2 rounded-md bg-primary px-3 text-xs font-semibold text-primary-foreground disabled:opacity-60">{running ? <RefreshCw size={14} className="animate-spin"/>:<Play size={14}/>}Run diagnostic</button>
        </div>
      </div>
      <div className="flex flex-col justify-between gap-3 p-4 sm:flex-row sm:items-center">
        <div><div className="text-xs text-muted-foreground">Current ensemble regime</div><div className="mt-1 flex flex-wrap items-center gap-3"><span className="text-2xl font-semibold tracking-tight">{market.regime}</span><span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">{market.confidence}% confidence</span></div><p className="mt-2 max-w-3xl text-sm text-muted-foreground">{market.summary}</p></div>
        <div className="shrink-0 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300">Sample inference · Python API pending</div>
      </div>
    </section>

    <section className="grid grid-cols-2 gap-3 xl:grid-cols-4">{market.probabilities.map(item => <div key={item.label} className="rounded-lg border border-border bg-card p-4 shadow-sm"><div className="flex items-start justify-between gap-2"><div><div className="text-xs font-semibold">{item.label}</div><div className="mt-1 text-[11px] text-muted-foreground">{item.note}</div></div><div className="text-xl font-semibold tabular-nums" style={{color:item.color}}>{item.value}%</div></div><div className="mt-4 h-1.5 overflow-hidden rounded bg-secondary"><div className="h-full rounded" style={{width:`${item.value}%`,background:item.color}}/></div></div>)}</section>

    <section className="grid grid-cols-1 gap-4 xl:grid-cols-[1.5fr_.5fr]">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><div className="mb-3 flex flex-wrap items-end justify-between gap-2"><div><h3 className="text-sm font-semibold">Regime Timeline</h3><p className="mt-0.5 text-xs text-muted-foreground">{market.asset} · {horizon} rolling classification with detected breakpoints</p></div><div className="text-right"><div className="font-semibold tabular-nums">{market.price}</div><div className="text-xs text-down">{market.change}</div></div></div><RegimeChart seed={marketIndex * 9}/></div>
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><div className="flex items-center gap-2"><AlertTriangle size={16} className="text-amber-500"/><h3 className="text-sm font-semibold">Break Monitor</h3></div><div className="mt-4 space-y-4">{[
        ['Variance shift','Nov 14','Moderate','bg-amber-500'],['Mean break','Sep 26','Low','bg-blue-500'],['Bubble signal','Aug 08','Watch','bg-amber-500'],['Volatility jump','Apr 04','Resolved','bg-green-500'],
      ].map(([label,date,status,color]) => <div key={label} className="flex items-center gap-3"><span className={`h-2 w-2 rounded-full ${color}`}/><div className="flex-1"><div className="text-xs font-semibold">{label}</div><div className="text-[11px] text-muted-foreground">{date}</div></div><span className="text-[11px] font-medium text-muted-foreground">{status}</span></div>)}</div></div>
    </section>

    <section className="overflow-hidden rounded-lg border border-border bg-card shadow-sm"><div className="flex items-center justify-between border-b border-border p-4"><div><h3 className="text-sm font-semibold">Model Consensus</h3><p className="mt-0.5 text-xs text-muted-foreground">Independent model outputs before ensemble calibration</p></div><span className="text-xs text-muted-foreground">5 models</span></div><div className="overflow-x-auto"><table className="w-full min-w-[820px] text-xs"><thead className="bg-secondary/70 text-muted-foreground"><tr>{['Model','Family','Current Signal','Probability','Status','Specification'].map(label => <th key={label} className="px-4 py-3 text-left">{label}</th>)}</tr></thead><tbody>{modelRows.map(item => <tr key={item.model} className="border-t border-border"><td className="px-4 py-3 font-semibold">{item.model}</td><td className="px-4 py-3 text-muted-foreground">{item.family}</td><td className="px-4 py-3">{item.signal}</td><td className="px-4 py-3"><div className="flex items-center gap-2"><div className="h-1.5 w-16 overflow-hidden rounded bg-secondary"><div className="h-full bg-primary" style={{width:`${item.probability}%`}}/></div><b className="tabular-nums">{item.probability}%</b></div></td><td className="px-4 py-3"><span className={`rounded px-2 py-1 text-[11px] font-semibold ${item.status === 'Watch' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/30 dark:text-amber-300':'bg-green-100 text-green-800 dark:bg-green-950/30 dark:text-green-300'}`}>{item.status}</span></td><td className="px-4 py-3 text-muted-foreground">{item.description}</td></tr>)}</tbody></table></div></section>

    <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><div className="flex items-center gap-2"><Gauge size={16} className="text-primary"/><h3 className="text-sm font-semibold">Feature Contributions</h3></div><div className="mt-4 space-y-3">{features.map(([label,value,direction]) => <div key={String(label)} className="grid grid-cols-[145px_1fr_62px] items-center gap-3 text-xs"><span className="truncate text-muted-foreground">{label}</span><div className="h-2 overflow-hidden rounded bg-secondary"><div className={`h-full rounded ${direction === 'Negative' ? 'bg-red-500':direction === 'Positive' ? 'bg-blue-500':'bg-slate-400'}`} style={{width:`${value}%`}}/></div><span className={`text-right font-semibold ${direction === 'Negative' ? 'text-down':direction === 'Positive' ? 'text-primary':'text-muted-foreground'}`}>{direction}</span></div>)}</div></div>
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><div className="flex items-center gap-2"><Waves size={16} className="text-primary"/><h3 className="text-sm font-semibold">Diagnostics &amp; Reliability</h3></div><div className="mt-4 grid grid-cols-2 gap-3">{[['Ensemble agreement','72%'],['Out-of-sample accuracy','64.8%'],['Last detected break','38 sessions'],['Signal half-life','12 sessions']].map(([label,value]) => <div key={label} className="rounded-md bg-secondary/60 p-3"><div className="text-[11px] text-muted-foreground">{label}</div><div className="mt-1 text-lg font-semibold tabular-nums">{value}</div></div>)}</div><div className="mt-4 flex items-start gap-2 rounded-md border border-border p-3"><CheckCircle2 size={15} className="mt-0.5 shrink-0 text-up"/><p className="text-xs leading-5 text-muted-foreground">No single model dominates the ensemble. Probabilities are calibrated on rolling out-of-sample windows and should be interpreted as monitoring signals, not trading advice.</p></div></div>
    </section>

    <div className="flex flex-col gap-1 border-t border-border pt-3 text-[11px] text-muted-foreground sm:flex-row sm:justify-between"><span>Model inputs: daily returns · realized volatility · breadth · volume · rates · credit spreads</span><span>Last evaluated: {updated}</span></div>
  </div>;
}
