import React, { useState, useMemo, useCallback } from "react";
import {
  PieChart, Pie, Cell, Tooltip as RTooltip, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend, ReferenceDot,
  BarChart, Bar,
} from "recharts";
import {
  portfolioAssets, correlationMatrix, computeMVOWeights, computeHRPWeights,
  computeNCOWeights, computeBLWeights, computePortfolioMetrics,
  generateEfficientFrontier,
  type PortfolioMethod, type MVOParams, type HRPParams, type NCOParams, type BLParams,
} from "../../data/mockData";
import { Info, ChevronDown, ChevronUp } from "lucide-react";

const fmt2 = (v: number) => v.toFixed(2);
const fmt1 = (v: number) => v.toFixed(1);
const pct  = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

const METHOD_META: Record<PortfolioMethod, { label: string; desc: string; color: string }> = {
  mvo: { label: 'Markowitz MVO', desc: 'Mean-variance optimization using expected returns and covariance matrix', color: '#1A56DB' },
  hrp: { label: 'HRP',           desc: 'Hierarchical Risk Parity with hierarchical clustering for balanced risk distribution',     color: '#16A34A' },
  nco: { label: 'NCO',           desc: 'Two-stage optimization across and within clusters',             color: '#F59E0B' },
  bl:  { label: 'Black-Litterman', desc: 'Bayesian blending of investor views with market equilibrium portfolio',          color: '#8B5CF6' },
};

// ─── Slider ───────────────────────────────────────────────────────────────────
function ParamSlider({ label, value, min, max, step, unit = '', onChange }: {
  label: string; value: number; min: number; max: number; step: number; unit?: string; onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-[11px] text-muted-foreground">{label}</span>
        <span className="text-[11px] font-mono font-semibold text-foreground">{value}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded appearance-none bg-secondary accent-primary cursor-pointer"
      />
      <div className="flex justify-between text-[9px] text-muted-foreground mt-0.5">
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

// ─── MVO Parameters ───────────────────────────────────────────────────────────
function MVOParamPanel({ params, setParams }: { params: MVOParams; setParams: (p: MVOParams) => void }) {
  return (
    <div className="space-y-3">
      <ParamSlider label="Risk Aversion (λ)" value={params.riskAversion} min={0.5} max={5} step={0.1}
        onChange={v => setParams({ ...params, riskAversion: v })} />
      <ParamSlider label="Min Weight" value={params.minWeight * 100} min={0} max={10} step={0.5} unit="%"
        onChange={v => setParams({ ...params, minWeight: v / 100 })} />
      <ParamSlider label="Max Weight" value={params.maxWeight * 100} min={20} max={100} step={1} unit="%"
        onChange={v => setParams({ ...params, maxWeight: v / 100 })} />
      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" checked={params.longOnly}
          onChange={e => setParams({ ...params, longOnly: e.target.checked })}
          className="accent-primary" />
        <span className="text-[11px] text-muted-foreground">Long-only Constraint (no short selling)</span>
      </label>
      <div className="bg-accent rounded p-2 text-[10px] text-muted-foreground">
        Higher λ increases allocation to safe assets (bonds·gold); lower λ favors equities
      </div>
    </div>
  );
}

// ─── HRP Parameters ───────────────────────────────────────────────────────────
function HRPParamPanel({ params, setParams }: { params: HRPParams; setParams: (p: HRPParams) => void }) {
  return (
    <div className="space-y-3">
      <div>
        <div className="text-[11px] text-muted-foreground mb-1.5">Linkage Method</div>
        <div className="grid grid-cols-2 gap-1">
          {['ward', 'complete', 'single', 'average'].map(v => (
            <button key={v} onClick={() => setParams({ ...params, linkage: v })}
              className={`text-[10px] py-1 rounded border transition-colors ${params.linkage === v ? 'bg-primary text-white border-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <div>
        <div className="text-[11px] text-muted-foreground mb-1.5">Distance Metric</div>
        <div className="grid grid-cols-3 gap-1">
          {['pearson', 'spearman', 'kendall'].map(v => (
            <button key={v} onClick={() => setParams({ ...params, distanceMetric: v })}
              className={`text-[10px] py-1 rounded border transition-colors ${params.distanceMetric === v ? 'bg-primary text-white border-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <div className="bg-accent rounded p-2 text-[10px] text-muted-foreground">
        Ward linkage minimizes within-cluster variance, generally yielding the most balanced clustering
      </div>
    </div>
  );
}

// ─── NCO Parameters ───────────────────────────────────────────────────────────
function NCOParamPanel({ params, setParams }: { params: NCOParams; setParams: (p: NCOParams) => void }) {
  return (
    <div className="space-y-3">
      <ParamSlider label="Number of Clusters" value={params.nClusters} min={2} max={6} step={1}
        onChange={v => setParams({ ...params, nClusters: v })} />
      <div>
        <div className="text-[11px] text-muted-foreground mb-1.5">Within-Cluster Optimization</div>
        <div className="grid grid-cols-3 gap-1">
          {[['mvo', 'MVO'], ['ivp', 'IVP'], ['equal', 'Equal']].map(([v, l]) => (
            <button key={v} onClick={() => setParams({ ...params, withinCluster: v })}
              className={`text-[10px] py-1 rounded border transition-colors ${params.withinCluster === v ? 'bg-primary text-white border-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>
              {l}
            </button>
          ))}
        </div>
      </div>
      <div>
        <div className="text-[11px] text-muted-foreground mb-1.5">Covariance Estimator</div>
        <div className="grid grid-cols-3 gap-1">
          {[['sample', 'Sample'], ['ledoit', 'Ledoit-Wolf'], ['oas', 'OAS']].map(([v, l]) => (
            <button key={v} onClick={() => setParams({ ...params, covEstimator: v })}
              className={`text-[10px] py-1 rounded border transition-colors ${params.covEstimator === v ? 'bg-primary text-white border-primary' : 'border-border text-muted-foreground hover:text-foreground'}`}>
              {l}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Black-Litterman Parameters ───────────────────────────────────────────────
function BLParamPanel({ params, setParams }: { params: BLParams; setParams: (p: BLParams) => void }) {
  const updateView = (i: number, field: string, value: any) => {
    const views = [...params.views];
    views[i] = { ...views[i], [field]: value };
    setParams({ ...params, views });
  };

  return (
    <div className="space-y-3">
      <ParamSlider label="Market Risk Aversion (δ)" value={params.delta} min={1} max={5} step={0.1}
        onChange={v => setParams({ ...params, delta: v })} />
      <ParamSlider label="Uncertainty (τ)" value={params.tau} min={0.01} max={0.5} step={0.01}
        onChange={v => setParams({ ...params, tau: v })} />
      <div>
        <div className="text-[11px] font-semibold text-muted-foreground mb-1.5">Investor Views</div>
        <div className="space-y-2">
          {params.views.map((view, i) => (
            <div key={i} className="bg-secondary rounded p-2 space-y-1.5">
              <div className="flex items-center gap-1.5">
                <select
                  value={view.assetId}
                  onChange={e => updateView(i, 'assetId', e.target.value)}
                  className="flex-1 text-[10px] bg-card border border-border rounded px-1 py-0.5 text-foreground"
                >
                  {portfolioAssets.map(a => (
                    <option key={a.id} value={a.id}>{a.name} ({a.ticker})</option>
                  ))}
                </select>
                <select
                  value={view.direction}
                  onChange={e => updateView(i, 'direction', e.target.value)}
                  className="text-[10px] bg-card border border-border rounded px-1 py-0.5 text-foreground"
                >
                  <option value="up">Bullish</option>
                  <option value="down">Bearish</option>
                </select>
              </div>
              <div className="flex gap-2 text-[10px]">
                <div className="flex-1">
                  <div className="text-muted-foreground mb-0.5">Expected Excess Return (%)</div>
                  <input type="number" min={1} max={30} value={view.magnitude}
                    onChange={e => updateView(i, 'magnitude', parseFloat(e.target.value) || 0)}
                    className="w-full bg-card border border-border rounded px-1.5 py-0.5 font-mono text-foreground"
                  />
                </div>
                <div className="flex-1">
                  <div className="text-muted-foreground mb-0.5">Confidence (%)</div>
                  <input type="number" min={10} max={100} value={view.confidence}
                    onChange={e => updateView(i, 'confidence', parseFloat(e.target.value) || 0)}
                    className="w-full bg-card border border-border rounded px-1.5 py-0.5 font-mono text-foreground"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Asset Selector ───────────────────────────────────────────────────────────
function AssetSelector({ active, setActive }: { active: Set<string>; setActive: (s: Set<string>) => void }) {
  const toggle = (id: string) => {
    const next = new Set(active);
    if (next.has(id)) { if (next.size > 2) next.delete(id); }
    else next.add(id);
    setActive(next);
  };
  return (
    <div className="bg-card border border-border rounded p-3">
      <div className="text-[11px] font-semibold text-foreground mb-2">Asset Universe</div>
      <div className="space-y-1">
        {portfolioAssets.map(a => (
          <label key={a.id} className="flex items-center gap-2 cursor-pointer group">
            <input type="checkbox" checked={active.has(a.id)} onChange={() => toggle(a.id)}
              className="accent-primary" />
            <span className="w-2 h-2 rounded-sm" style={{ background: a.color }} />
            <span className="text-[11px] text-foreground flex-1">{a.name}</span>
            <span className="text-[10px] font-mono text-muted-foreground">{a.ticker}</span>
          </label>
        ))}
      </div>
      <div className="mt-2 text-[10px] text-muted-foreground">Minimum 2 assets required</div>
    </div>
  );
}

// ─── Weights Pie ──────────────────────────────────────────────────────────────
function WeightsPie({ weights }: { weights: Record<string, number> }) {
  const data = portfolioAssets
    .filter(a => (weights[a.id] ?? 0) > 0.001)
    .map(a => ({ name: a.name, value: parseFloat((weights[a.id] * 100).toFixed(1)), color: a.color }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="text-xs font-bold text-foreground mb-3">Optimal Portfolio Weights</div>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
            dataKey="value" nameKey="name" label={({ name, value }) => value > 3 ? `${value}%` : ''}
            labelLine={false}
          >
            {data.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={entry.color} />
            ))}
          </Pie>
          <RTooltip
            contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 11 }}
            formatter={(v: any, name: string) => [`${v}%`, name]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Metrics Panel ────────────────────────────────────────────────────────────
function MetricsPanel({ metrics }: { metrics: ReturnType<typeof computePortfolioMetrics> }) {
  const rows = [
    { label: 'Expected Annual Return', value: `${fmt2(metrics.ret)}%`,    pos: metrics.ret > 0, highlight: true },
    { label: 'Annual Volatility',      value: `${fmt2(metrics.vol)}%`,    pos: false, highlight: false },
    { label: 'Sharpe Ratio',           value: fmt2(metrics.sharpe),       pos: metrics.sharpe > 1, highlight: true },
    { label: 'Max Drawdown (MDD)',      value: `${fmt2(metrics.maxDD)}%`, pos: false, highlight: false },
    { label: 'Calmar Ratio',           value: fmt2(metrics.calmar),        pos: metrics.calmar > 0.5, highlight: false },
    { label: 'Sortino Ratio',          value: fmt2(metrics.sortino),       pos: metrics.sortino > 1, highlight: false },
    { label: 'VaR 95% (1M)',           value: `${fmt2(metrics.var95)}%`,  pos: false, highlight: false },
    { label: 'CVaR 95% (1M)',          value: `${fmt2(metrics.cvar95)}%`, pos: false, highlight: false },
  ];

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="text-xs font-bold text-foreground mb-3">Performance Metrics</div>
      <div className="grid grid-cols-2 gap-1.5">
        {rows.map(row => (
          <div key={row.label} className={`rounded p-2 ${row.highlight ? 'bg-accent' : 'bg-secondary'}`}>
            <div className="text-[10px] text-muted-foreground">{row.label}</div>
            <div className={`text-sm font-mono font-bold ${
              row.highlight ? (row.pos ? 'text-up' : 'text-down') : 'text-foreground'
            }`}>{row.value}</div>
          </div>
        ))}
      </div>
      <div className="mt-2 text-[10px] text-muted-foreground bg-secondary rounded p-1.5">
        Risk-free rate {fmt2(metrics.rf)}% assumed · Annual basis
      </div>
    </div>
  );
}

// ─── Weights Table ────────────────────────────────────────────────────────────
function WeightsTable({ weights }: { weights: Record<string, number> }) {
  const rows = portfolioAssets
    .filter(a => (weights[a.id] ?? 0) > 0.0005)
    .map(a => ({
      ...a,
      w: weights[a.id],
      riskContrib: weights[a.id] * a.volatility,
    }))
    .sort((a, b) => b.w - a.w);

  return (
    <div className="bg-card border border-border rounded overflow-hidden">
      <div className="px-3 py-2 bg-secondary border-b border-border">
        <span className="text-xs font-bold text-foreground">Asset Allocation Details</span>
      </div>
      <table className="w-full text-xs">
        <thead className="bg-secondary/50">
          <tr>
            {['Asset', 'Ticker', 'Region', 'Weight', 'Exp. Return', 'Volatility', 'Risk Contribution'].map(h => (
              <th key={h} className="text-left px-3 py-1.5 text-muted-foreground font-semibold whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.id} className="border-t border-border hover:bg-secondary/50">
              <td className="px-3 py-2">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-sm shrink-0" style={{ background: row.color }} />
                  <span className="font-semibold text-foreground">{row.name}</span>
                </div>
              </td>
              <td className="px-3 py-2 font-mono text-muted-foreground">{row.ticker}</td>
              <td className="px-3 py-2 text-muted-foreground">{row.region}</td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-secondary rounded-sm overflow-hidden" style={{ minWidth: 60 }}>
                    <div className="h-full rounded-sm" style={{ width: `${row.w * 100}%`, background: row.color }} />
                  </div>
                  <span className="font-mono font-bold text-foreground w-10 text-right">{(row.w * 100).toFixed(1)}%</span>
                </div>
              </td>
              <td className="px-3 py-2 font-mono text-up">{row.expectedReturn.toFixed(1)}%</td>
              <td className="px-3 py-2 font-mono text-muted-foreground">{row.volatility.toFixed(1)}%</td>
              <td className="px-3 py-2 font-mono text-foreground">{row.riskContrib.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Efficient Frontier ───────────────────────────────────────────────────────
function EfficientFrontierChart({ activeIds, optWeights, method }: {
  activeIds: string[]; optWeights: Record<string, number>; method: PortfolioMethod;
}) {
  const frontier = useMemo(() => generateEfficientFrontier(activeIds), [activeIds]);
  const assets   = portfolioAssets.filter(a => activeIds.includes(a.id));
  const metrics  = computePortfolioMetrics(optWeights);
  const optimal  = [{ x: parseFloat(metrics.vol.toFixed(2)), y: parseFloat(metrics.ret.toFixed(2)), name: 'Optimal Portfolio' }];
  const assetPts = assets.map(a => ({ x: a.volatility, y: a.expectedReturn, name: a.name }));

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="text-xs font-bold text-foreground mb-1">Efficient Frontier</div>
      <div className="text-[10px] text-muted-foreground mb-3">Risk-return trade-off curve · Star = Optimal Portfolio</div>
      <ResponsiveContainer width="100%" height={240}>
        <ScatterChart margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="x" type="number" name="Volatility" unit="%" domain={['auto', 'auto']}
            tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
            label={{ value: 'Annual Volatility (%)', position: 'insideBottom', offset: -2, fontSize: 10, fill: 'var(--muted-foreground)' }}
          />
          <YAxis
            dataKey="y" type="number" name="Return" unit="%" domain={['auto', 'auto']}
            tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }} width={40}
            label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft', fontSize: 10, fill: 'var(--muted-foreground)' }}
          />
          <RTooltip
            contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 11 }}
            formatter={(v: any, n: string) => [`${parseFloat(v).toFixed(2)}%`, n]}
          />
          <Scatter key="frontier-scatter" name="Efficient Frontier" data={frontier} fill="var(--primary)" fillOpacity={0.7} line={{ stroke: 'var(--primary)', strokeWidth: 2 }} lineType="fitting" shape="circle" />
          <Scatter key="assets-scatter" name="Individual Assets" data={assetPts} fill="var(--muted-foreground)" fillOpacity={0.6} shape="circle" />
          <Scatter key="optimal-scatter" name="Optimal Portfolio" data={optimal} fill="var(--up)" shape="star" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Correlation Heatmap ──────────────────────────────────────────────────────
function CorrelationHeatmap({ activeIds }: { activeIds: string[] }) {
  const active = portfolioAssets.filter(a => activeIds.includes(a.id));
  const n = active.length;
  if (n < 2) return null;

  const cellSize = Math.min(36, Math.floor(340 / n));
  const labelW   = 56;
  const svgW     = labelW + n * cellSize;
  const svgH     = labelW + n * cellSize;

  const getColor = (val: number) => {
    const abs = Math.abs(val);
    if (val > 0) return `rgba(26,86,219,${abs * 0.8})`;
    return `rgba(220,38,38,${abs * 0.8})`;
  };

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="text-xs font-bold text-foreground mb-1">Asset Correlation Heatmap</div>
      <div className="text-[10px] text-muted-foreground mb-3">Blue: Positive Correlation · Red: Negative Correlation</div>
      <div className="overflow-x-auto">
        <svg width={svgW} height={svgH} style={{ fontFamily: 'JetBrains Mono, monospace' }}>
          {active.map((a, i) => {
            const aIdx = portfolioAssets.findIndex(x => x.id === a.id);
            return active.map((b, j) => {
              const bIdx = portfolioAssets.findIndex(x => x.id === b.id);
              const val  = correlationMatrix[aIdx]?.[bIdx] ?? 0;
              const x    = labelW + j * cellSize;
              const y    = i * cellSize;
              return (
                <g key={`${i}-${j}`}>
                  <rect x={x} y={y} width={cellSize} height={cellSize}
                    fill={getColor(val)} stroke="var(--border)" strokeWidth={0.5} />
                  {cellSize >= 26 && (
                    <text x={x + cellSize / 2} y={y + cellSize / 2 + 3}
                      textAnchor="middle" fontSize={8} fill={Math.abs(val) > 0.5 ? 'white' : 'var(--foreground)'}
                      fontWeight={i === j ? 700 : 400}>
                      {val.toFixed(2)}
                    </text>
                  )}
                </g>
              );
            });
          })}
          {active.map((a, i) => (
            <text key={`yl-${i}`} x={labelW - 4} y={i * cellSize + cellSize / 2 + 3}
              textAnchor="end" fontSize={9} fill="var(--muted-foreground)">
              {a.name.slice(0, 5)}
            </text>
          ))}
          {active.map((a, j) => (
            <text key={`xl-${j}`} x={labelW + j * cellSize + cellSize / 2}
              y={n * cellSize + 12} textAnchor="middle" fontSize={9} fill="var(--muted-foreground)">
              {a.ticker.slice(0, 4)}
            </text>
          ))}
        </svg>
      </div>
      <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground">
        <span>Correlation range: -1 (perfect inverse) ~ +1 (perfect positive)</span>
      </div>
    </div>
  );
}

// ─── Method Comparison Bar ────────────────────────────────────────────────────
function MethodComparison({ activeIds }: { activeIds: string[] }) {
  const defMVO = { riskAversion: 2, minWeight: 0, maxWeight: 0.4, longOnly: true };
  const defHRP = { linkage: 'ward', distanceMetric: 'pearson' };
  const defNCO = { nClusters: 3, withinCluster: 'mvo', covEstimator: 'sample' };
  const defBL  = { delta: 2.5, tau: 0.05, views: [] };

  const results = useMemo(() => {
    const mvoW  = computeMVOWeights(defMVO, activeIds);
    const hrpW  = computeHRPWeights(defHRP, activeIds);
    const ncoW  = computeNCOWeights(defNCO, activeIds);
    const blW   = computeBLWeights(defBL, activeIds);
    return {
      mvo: computePortfolioMetrics(mvoW),
      hrp: computePortfolioMetrics(hrpW),
      nco: computePortfolioMetrics(ncoW),
      bl:  computePortfolioMetrics(blW),
    };
  }, [activeIds]);

  const data = (['mvo', 'hrp', 'nco', 'bl'] as PortfolioMethod[]).map(m => ({
    name: METHOD_META[m].label.split(' ')[0],
    return: parseFloat(results[m].ret.toFixed(2)),
    vol:    parseFloat(results[m].vol.toFixed(2)),
    sharpe: parseFloat(results[m].sharpe.toFixed(3)),
    fill:   METHOD_META[m].color,
  }));

  return (
    <div className="bg-card border border-border rounded p-4">
      <div className="text-xs font-bold text-foreground mb-3">Method Comparison (Default Parameters)</div>
      <div className="grid grid-cols-3 gap-4">
        {(['return', 'vol', 'sharpe'] as const).map((metric, mi) => {
          const labels = ['Expected Return (%)', 'Volatility (%)', 'Sharpe Ratio'];
          const chartData = data.map(d => ({ name: d.name, value: d[metric], fill: d.fill }));
          return (
            <div key={metric}>
              <div className="text-[10px] text-muted-foreground mb-1.5 text-center">{labels[mi]}</div>
              <ResponsiveContainer width="100%" height={110}>
                <BarChart data={chartData} barSize={24}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }} width={32} />
                  <RTooltip
                    contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 11 }}
                    formatter={(v: any) => [parseFloat(v).toFixed(3), labels[mi]]}
                  />
                  <Bar key={`bar-${metric}`} dataKey="value" name={labels[mi]}>
                    {chartData.map((entry, i) => <Cell key={`cell-${i}`} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Default params ───────────────────────────────────────────────────────────
const DEFAULT_MVO: MVOParams = { riskAversion: 2, minWeight: 0, maxWeight: 0.4, longOnly: true };
const DEFAULT_HRP: HRPParams = { linkage: 'ward', distanceMetric: 'pearson' };
const DEFAULT_NCO: NCOParams = { nClusters: 3, withinCluster: 'mvo', covEstimator: 'sample' };
const DEFAULT_BL:  BLParams  = {
  delta: 2.5, tau: 0.05,
  views: [
    { assetId: 'us_eq', direction: 'up',   magnitude: 8, confidence: 70 },
    { assetId: 'em_eq', direction: 'up',   magnitude: 12, confidence: 50 },
    { assetId: 'us_bd', direction: 'down', magnitude: 5, confidence: 60 },
  ],
};

// ─── Main ─────────────────────────────────────────────────────────────────────
export function AssetAllocationTab() {
  const [method, setMethod]     = useState<PortfolioMethod>('mvo');
  const [activeIds, setActiveIds] = useState(new Set(portfolioAssets.map(a => a.id)));
  const [mvoP, setMvoP]         = useState(DEFAULT_MVO);
  const [hrpP, setHrpP]         = useState(DEFAULT_HRP);
  const [ncoP, setNcoP]         = useState(DEFAULT_NCO);
  const [blP,  setBlP]          = useState(DEFAULT_BL);

  const activeIdsList = useMemo(() => Array.from(activeIds), [activeIds]);

  const weights = useMemo(() => {
    switch (method) {
      case 'mvo': return computeMVOWeights(mvoP, activeIdsList);
      case 'hrp': return computeHRPWeights(hrpP, activeIdsList);
      case 'nco': return computeNCOWeights(ncoP, activeIdsList);
      case 'bl':  return computeBLWeights(blP, activeIdsList);
    }
  }, [method, mvoP, hrpP, ncoP, ncoP, blP, activeIdsList]);

  const metrics = useMemo(() => computePortfolioMetrics(weights), [weights]);

  const methodColor = METHOD_META[method].color;

  return (
    <div className="p-4 space-y-4 max-w-screen-2xl mx-auto">

      {/* Method Selector */}
      <div className="flex items-start gap-3 flex-wrap">
        {(Object.keys(METHOD_META) as PortfolioMethod[]).map(m => (
          <button
            key={m}
            onClick={() => setMethod(m)}
            className={`flex flex-col items-start px-3 py-2 rounded border transition-all text-left ${
              method === m
                ? 'border-primary bg-accent text-foreground shadow-sm'
                : 'border-border text-muted-foreground hover:text-foreground hover:border-muted-foreground'
            }`}
          >
            <span className="text-xs font-bold">{METHOD_META[m].label}</span>
            <span className="text-[10px] leading-tight mt-0.5 hidden md:block max-w-48 text-muted-foreground">{METHOD_META[m].desc.slice(0, 50)}…</span>
          </button>
        ))}
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">

        {/* Left: Parameters + Asset Universe */}
        <div className="xl:col-span-1 space-y-3">
          <div className="bg-card border border-border rounded p-4">
            <div className="text-xs font-bold text-foreground mb-3 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-sm" style={{ background: methodColor }} />
              {METHOD_META[method].label} Parameters
            </div>
            {method === 'mvo' && <MVOParamPanel params={mvoP} setParams={setMvoP} />}
            {method === 'hrp' && <HRPParamPanel params={hrpP} setParams={setHrpP} />}
            {method === 'nco' && <NCOParamPanel params={ncoP} setParams={setNcoP} />}
            {method === 'bl'  && <BLParamPanel  params={blP}  setParams={setBlP}  />}
          </div>
          <AssetSelector active={activeIds} setActive={setActiveIds} />
        </div>

        {/* Right: Results */}
        <div className="xl:col-span-3 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <WeightsPie weights={weights} />
            <MetricsPanel metrics={metrics} />
          </div>
          <WeightsTable weights={weights} />
        </div>
      </div>

      {/* Bottom: Frontier + Heatmap + Comparison */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <EfficientFrontierChart activeIds={activeIdsList} optWeights={weights} method={method} />
        <CorrelationHeatmap activeIds={activeIdsList} />
      </div>
      <MethodComparison activeIds={activeIdsList} />
    </div>
  );
}
