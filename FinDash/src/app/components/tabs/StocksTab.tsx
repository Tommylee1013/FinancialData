import { useMemo, useState } from 'react';
import { ArrowDownRight, ArrowUpRight, Building2, CalendarDays, ExternalLink, Search, Star, Users } from 'lucide-react';
import { TimeSeriesChart } from '../TimeSeriesChart';
import { generateOHLC } from '../../data/mockData';

type Stock = {
  symbol: string; name: string; exchange: string; currency: string;
  price: number; change: number; changePct: number; afterHours: number;
  marketCap: string; pe: number; eps: number; beta: number; dividend: string;
  dayRange: string; yearRange: string; volume: string; avgVolume: string;
  target: number; sector: string;
};

const stocks: Stock[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', exchange: 'NasdaqGS', currency: 'USD', price: 228.18, change: 2.72, changePct: 1.21, afterHours: 0.14, marketCap: '3.45T', pe: 34.72, eps: 6.57, beta: 1.18, dividend: '1.00 (0.44%)', dayRange: '224.31 – 229.80', yearRange: '164.08 – 237.49', volume: '47.8M', avgVolume: '52.3M', target: 245.60, sector: 'Technology' },
  { symbol: 'MSFT', name: 'Microsoft Corporation', exchange: 'NasdaqGS', currency: 'USD', price: 442.62, change: -1.84, changePct: -0.41, afterHours: 0.08, marketCap: '3.29T', pe: 36.41, eps: 12.16, beta: 0.89, dividend: '3.32 (0.75%)', dayRange: '439.22 – 446.18', yearRange: '344.77 – 468.35', volume: '18.2M', avgVolume: '21.1M', target: 485.20, sector: 'Technology' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation', exchange: 'NasdaqGS', currency: 'USD', price: 141.25, change: 3.16, changePct: 2.29, afterHours: -0.11, marketCap: '3.46T', pe: 55.83, eps: 2.53, beta: 1.66, dividend: '0.04 (0.03%)', dayRange: '137.48 – 142.89', yearRange: '45.01 – 152.89', volume: '219.4M', avgVolume: '276.8M', target: 165.40, sector: 'Semiconductors' },
  { symbol: '005930.KS', name: 'Samsung Electronics Co., Ltd.', exchange: 'KSE', currency: 'KRW', price: 73500, change: 900, changePct: 1.24, afterHours: 0, marketCap: '438.8T', pe: 24.16, eps: 3042, beta: 0.82, dividend: '1,444 (1.96%)', dayRange: '72,400 – 74,100', yearRange: '53,000 – 88,800', volume: '15.7M', avgVolume: '17.2M', target: 91000, sector: 'Technology' },
];

const financials = [
  ['Total Revenue', '394.3B', '383.3B', '365.8B', '274.5B'],
  ['Gross Profit', '180.7B', '169.1B', '152.8B', '105.1B'],
  ['Operating Income', '123.2B', '114.3B', '119.4B', '66.3B'],
  ['Net Income', '100.9B', '97.0B', '99.8B', '57.4B'],
  ['Diluted EPS', '6.08', '6.13', '6.11', '3.28'],
  ['Free Cash Flow', '99.6B', '99.6B', '111.4B', '73.4B'],
];

const ratios = [
  ['Trailing P/E', '34.72'], ['Forward P/E', '30.41'], ['Price / Sales', '8.76'],
  ['Price / Book', '47.32'], ['EV / EBITDA', '25.84'], ['Profit Margin', '25.31%'],
  ['Operating Margin', '31.17%'], ['Return on Assets', '22.61%'], ['Return on Equity', '157.41%'],
  ['Debt / Equity', '187.14%'], ['Current Ratio', '0.89'], ['Revenue Growth', '6.07%'],
];

const ratings = [
  { date: 'Nov 18', firm: 'Morgan Stanley', action: 'Reiterates', rating: 'Overweight', target: '$273 → $275', tone: 'text-up' },
  { date: 'Nov 12', firm: 'Mizuho', action: 'Maintains', rating: 'Outperform', target: '$260', tone: 'text-up' },
  { date: 'Nov 04', firm: 'Barclays', action: 'Reiterates', rating: 'Underweight', target: '$186 → $184', tone: 'text-down' },
  { date: 'Oct 31', firm: 'JPMorgan', action: 'Maintains', rating: 'Overweight', target: '$265', tone: 'text-up' },
];

const peers = [
  { symbol: 'MSFT', name: 'Microsoft', price: '442.62', change: -0.41, pe: '36.41', margin: '35.61%' },
  { symbol: 'GOOGL', name: 'Alphabet', price: '175.98', change: 0.86, pe: '25.18', margin: '27.74%' },
  { symbol: 'NVDA', name: 'NVIDIA', price: '141.25', change: 2.29, pe: '55.83', margin: '55.04%' },
  { symbol: 'SONY', name: 'Sony Group', price: '20.74', change: -0.32, pe: '18.92', margin: '9.84%' },
];

const news = [
  { time: '42m ago', source: 'Reuters', title: 'Apple supplier outlook lifts expectations for the holiday quarter', tag: 'News' },
  { time: '2h ago', source: 'FinDash Brief', title: 'Services revenue and margins remain the key drivers into FY2026', tag: 'Research' },
  { time: 'Yesterday', source: 'SEC', title: 'Form 4 — Statement of changes in beneficial ownership', tag: 'Filing' },
  { time: 'Nov 18', source: 'Company IR', title: 'Quarterly dividend and share repurchase update', tag: 'Corporate action' },
];

const events = [
  ['Jan 30, 2027', 'Q1 earnings release', 'EPS est. $2.35'],
  ['Feb 10, 2027', 'Ex-dividend date', '$0.25 estimated'],
  ['Feb 13, 2027', 'Dividend payment', 'Quarterly'],
];

const fmt = (value: number, currency: string) => currency === 'KRW'
  ? value.toLocaleString('ko-KR')
  : value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function StocksTab() {
  const [selected, setSelected] = useState(stocks[0]);
  const [query, setQuery] = useState('');
  const [section, setSection] = useState('Overview');
  const [watched, setWatched] = useState(false);
  const [period, setPeriod] = useState<'Annual' | 'Quarterly'>('Annual');
  const chartData = useMemo(() => generateOHLC(selected.price * 0.82, 120, selected.price * 0.018), [selected]);
  const up = selected.change >= 0;
  const filtered = stocks.filter(item => `${item.symbol} ${item.name}`.toLowerCase().includes(query.toLowerCase()));

  return <div className="mx-auto max-w-screen-2xl space-y-4 p-4 sm:p-6">
    <div className="rounded-lg border border-border bg-card shadow-sm">
      <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center">
        <div className="relative max-w-xl flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16}/>
          <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search stocks by symbol or company" className="h-10 w-full rounded-md border border-border bg-background pl-9 pr-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"/>
          {query && <div className="absolute left-0 right-0 top-11 z-20 overflow-hidden rounded-md border border-border bg-card shadow-xl">
            {filtered.map(item => <button key={item.symbol} onClick={() => { setSelected(item); setQuery(''); }} className="flex w-full items-center justify-between border-b border-border px-3 py-2.5 text-left last:border-0 hover:bg-secondary"><span><b className="text-sm">{item.symbol}</b><span className="ml-2 text-xs text-muted-foreground">{item.name}</span></span><span className="text-xs tabular-nums">{fmt(item.price, item.currency)}</span></button>)}
            {!filtered.length && <div className="p-4 text-xs text-muted-foreground">No matching sample stocks.</div>}
          </div>}
        </div>
        <div className="flex gap-2 overflow-x-auto">
          {stocks.map(item => <button key={item.symbol} onClick={() => setSelected(item)} className={`rounded-md border px-3 py-2 text-xs font-semibold transition-colors ${selected.symbol === item.symbol ? 'border-primary bg-primary text-primary-foreground' : 'border-border hover:bg-secondary'}`}>{item.symbol}</button>)}
        </div>
      </div>

      <div className="px-4 pt-4 sm:px-5">
        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
          <div>
            <div className="flex items-center gap-2"><h2 className="text-xl font-semibold tracking-tight">{selected.name} ({selected.symbol})</h2><button onClick={() => setWatched(value => !value)} aria-label={watched ? 'Remove from watchlist' : 'Add to watchlist'} className={`rounded-full border p-1.5 ${watched ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:text-primary'}`}><Star size={15} fill={watched ? 'currentColor' : 'none'}/></button></div>
            <div className="mt-1 text-xs text-muted-foreground">{selected.exchange} · Real-time sample price · {selected.currency} · {selected.sector}</div>
            <div className="mt-4 flex flex-wrap items-end gap-x-3 gap-y-1">
              <span className="text-4xl font-semibold tracking-tight tabular-nums">{fmt(selected.price, selected.currency)}</span>
              <span className={`mb-1 flex items-center text-sm font-semibold tabular-nums ${up ? 'text-up' : 'text-down'}`}>{up ? <ArrowUpRight size={16}/> : <ArrowDownRight size={16}/>} {up ? '+' : ''}{fmt(selected.change, selected.currency)} ({up ? '+' : ''}{selected.changePct.toFixed(2)}%)</span>
            </div>
            <div className="mt-1 text-xs text-muted-foreground">At close · After hours <span className={selected.afterHours >= 0 ? 'text-up' : 'text-down'}>{selected.afterHours >= 0 ? '+' : ''}{selected.afterHours.toFixed(2)}%</span></div>
          </div>
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300">Sample data · DB connection pending</div>
        </div>

        <div className="mt-5 flex gap-6 overflow-x-auto border-b border-border">
          {['Overview', 'Financials', 'Analysis', 'News & Filings'].map(item => <button key={item} onClick={() => setSection(item)} className={`border-b-2 pb-2.5 text-sm font-semibold whitespace-nowrap ${section === item ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}>{item}</button>)}
        </div>
      </div>
    </div>

    {section === 'Overview' && <>
    <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.65fr)_minmax(300px,.85fr)]">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between"><div><h3 className="text-sm font-semibold">Price Performance</h3><p className="mt-0.5 text-xs text-muted-foreground">Daily candles · Sample history</p></div><div className="flex gap-1">{['1D','5D','1M','6M','YTD','1Y'].map((period, index) => <button key={period} className={`rounded px-2 py-1 text-xs ${index === 4 ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary'}`}>{period}</button>)}</div></div>
        <TimeSeriesChart key={selected.symbol} data={chartData} height={390} initialMode="line" initialMonths={6}/>
      </div>
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <h3 className="text-sm font-semibold">Key Statistics</h3>
        <div className="mt-3 grid grid-cols-2 gap-x-5 text-xs">
          {[['Previous Close', fmt(selected.price - selected.change, selected.currency)], ['Day Range', selected.dayRange], ['52 Week Range', selected.yearRange], ['Volume', selected.volume], ['Avg. Volume', selected.avgVolume], ['Market Cap', selected.marketCap], ['Beta (5Y)', selected.beta.toFixed(2)], ['PE Ratio (TTM)', selected.pe.toFixed(2)], ['EPS (TTM)', selected.eps.toFixed(2)], ['Dividend & Yield', selected.dividend], ['1Y Target Est.', fmt(selected.target, selected.currency)]].map(([label,value]) => <div key={label} className="col-span-2 flex justify-between border-b border-border py-2.5"><span className="text-muted-foreground">{label}</span><span className="font-semibold tabular-nums">{value}</span></div>)}
        </div>
      </div>
    </section>

    <section className="grid grid-cols-1 gap-4 xl:grid-cols-[1.1fr_.9fr]">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="flex items-center gap-2"><Building2 size={16} className="text-primary"/><h3 className="text-sm font-semibold">Company Profile</h3></div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">Apple designs, manufactures and markets smartphones, personal computers, tablets, wearables and related services. Its ecosystem combines hardware, software and recurring digital services across global consumer markets.</p>
        <div className="mt-4 grid grid-cols-2 gap-3 text-xs md:grid-cols-4">{[['Sector', selected.sector], ['Industry', 'Consumer Electronics'], ['Employees', '164,000'], ['Fiscal year', 'September']].map(([label,value]) => <div key={label}><div className="text-muted-foreground">{label}</div><div className="mt-1 font-semibold">{value}</div></div>)}</div>
      </div>
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="flex items-center gap-2"><Users size={16} className="text-primary"/><h3 className="text-sm font-semibold">Ownership &amp; Flow</h3></div>
        <div className="mt-4 space-y-3">{[['Institutional ownership','61.4%'],['Insider ownership','0.1%'],['Short interest','0.7%'],['ETF ownership','22.8%']].map(([label,value],index) => <div key={label}><div className="mb-1 flex justify-between text-xs"><span className="text-muted-foreground">{label}</span><b>{value}</b></div><div className="h-1.5 rounded bg-secondary"><div className="h-full rounded bg-primary" style={{width:[61.4,3,7,22.8][index]+'%'}}/></div></div>)}</div>
      </div>
    </section>

    <section className="overflow-hidden rounded-lg border border-border bg-card shadow-sm"><div className="border-b border-border p-4"><h3 className="text-sm font-semibold">Peer Comparison</h3><p className="mt-0.5 text-xs text-muted-foreground">Price, valuation and profitability versus selected peers</p></div><div className="overflow-x-auto"><table className="w-full min-w-[620px] text-xs"><thead className="bg-secondary/70 text-muted-foreground"><tr>{['Company','Price','Daily Change','P/E','Profit Margin'].map(label => <th key={label} className="px-4 py-3 text-left">{label}</th>)}</tr></thead><tbody>{peers.map(item => <tr key={item.symbol} className="border-t border-border"><td className="px-4 py-3"><b>{item.symbol}</b><span className="ml-2 text-muted-foreground">{item.name}</span></td><td className="px-4 py-3 tabular-nums">${item.price}</td><td className={`px-4 py-3 font-semibold ${item.change >= 0 ? 'text-up':'text-down'}`}>{item.change >= 0 ? '+':''}{item.change.toFixed(2)}%</td><td className="px-4 py-3 tabular-nums">{item.pe}</td><td className="px-4 py-3 tabular-nums">{item.margin}</td></tr>)}</tbody></table></div></section>
    </>}

    {section === 'Financials' && <>
    <section className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border p-4"><div><h3 className="text-sm font-semibold">Financial Statements</h3><p className="mt-0.5 text-xs text-muted-foreground">Income statement highlights · USD unless noted</p></div><div className="flex rounded-md border border-border p-0.5">{(['Annual','Quarterly'] as const).map(item => <button key={item} onClick={() => setPeriod(item)} className={`rounded px-3 py-1 text-xs ${period === item ? 'bg-primary text-primary-foreground':'text-muted-foreground'}`}>{item}</button>)}</div></div>
      <div className="overflow-x-auto"><table className="w-full min-w-[700px] text-xs"><thead className="bg-secondary/70 text-muted-foreground"><tr><th className="px-4 py-3 text-left">Breakdown</th><th className="px-4 py-3 text-right">TTM</th><th className="px-4 py-3 text-right">FY 2024</th><th className="px-4 py-3 text-right">FY 2023</th><th className="px-4 py-3 text-right">FY 2022</th></tr></thead><tbody>{financials.map(row => <tr key={row[0]} className="border-t border-border"><td className="px-4 py-3 font-medium">{row[0]}</td>{row.slice(1).map((value,index) => <td key={index} className="px-4 py-3 text-right tabular-nums">{value}</td>)}</tr>)}</tbody></table></div>
    </section>

    <section className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div><h3 className="text-sm font-semibold">Financial Ratios</h3><p className="mt-0.5 text-xs text-muted-foreground">Valuation, profitability, leverage and growth</p></div>
      <div className="mt-4 grid grid-cols-2 gap-x-6 md:grid-cols-3 xl:grid-cols-4">{ratios.map(([label,value]) => <div key={label} className="flex items-center justify-between border-b border-border py-3 text-xs"><span className="text-muted-foreground">{label}</span><span className="font-semibold tabular-nums">{value}</span></div>)}</div>
    </section>

    <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><h3 className="text-sm font-semibold">Revenue &amp; Earnings Trend</h3><p className="mt-0.5 text-xs text-muted-foreground">Annual growth profile</p><div className="mt-5 flex h-44 items-end gap-5 border-b border-border px-4">{[['FY21',62,48],['FY22',78,57],['FY23',84,63],['FY24',92,69],['TTM',100,74]].map(([label,revenue,income]) => <div key={label} className="flex flex-1 items-end justify-center gap-1"><div className="w-5 rounded-t bg-primary/35" style={{height:`${revenue}%`}}/><div className="w-5 rounded-t bg-primary" style={{height:`${income}%`}}/><span className="absolute mt-6 hidden">{label}</span></div>)}</div><div className="mt-2 flex justify-around text-[11px] text-muted-foreground">{['FY21','FY22','FY23','FY24','TTM'].map(item => <span key={item}>{item}</span>)}</div></div>
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><h3 className="text-sm font-semibold">Earnings History</h3><p className="mt-0.5 text-xs text-muted-foreground">EPS actual versus consensus</p><div className="mt-4 space-y-4">{[['Q4 FY24','1.64','1.60','+2.5%'],['Q3 FY24','1.40','1.35','+3.7%'],['Q2 FY24','1.53','1.50','+2.0%'],['Q1 FY24','2.18','2.10','+3.8%']].map(row => <div key={row[0]} className="grid grid-cols-4 items-center text-xs"><b>{row[0]}</b><span className="text-muted-foreground">Est. {row[2]}</span><span>Actual {row[1]}</span><span className="text-right font-semibold text-up">{row[3]}</span></div>)}</div></div>
    </section>
    </>}

    {section === 'Analysis' && <>
    <section className="grid grid-cols-1 gap-4 xl:grid-cols-[.8fr_1.2fr]">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <h3 className="text-sm font-semibold">Analyst Price Targets</h3><div className="mt-1 text-xs text-muted-foreground">Based on 38 sample analyst opinions</div>
        <div className="mt-6 grid grid-cols-3 text-center"><div><div className="text-xs text-muted-foreground">Low</div><div className="mt-1 font-semibold tabular-nums">$184</div></div><div><div className="text-xs text-muted-foreground">Average</div><div className="mt-1 text-lg font-semibold text-primary tabular-nums">$245.60</div></div><div><div className="text-xs text-muted-foreground">High</div><div className="mt-1 font-semibold tabular-nums">$300</div></div></div>
        <div className="relative mt-5 h-2 rounded-full bg-gradient-to-r from-red-400 via-amber-300 to-green-500"><span className="absolute left-[56%] top-1/2 h-4 w-1 -translate-y-1/2 rounded bg-foreground"/></div>
        <div className="mt-6 grid grid-cols-5 gap-1 text-center text-[11px]"><div><b>11</b><span className="block text-muted-foreground">Strong Buy</span></div><div><b>17</b><span className="block text-muted-foreground">Buy</span></div><div><b>8</b><span className="block text-muted-foreground">Hold</span></div><div><b>2</b><span className="block text-muted-foreground">Sell</span></div><div><b>0</b><span className="block text-muted-foreground">Strong Sell</span></div></div>
      </div>
      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm"><div className="border-b border-border p-4"><h3 className="text-sm font-semibold">Upgrades &amp; Downgrades</h3><p className="mt-0.5 text-xs text-muted-foreground">Latest analyst rating actions</p></div><div className="overflow-x-auto"><table className="w-full min-w-[580px] text-xs"><thead className="bg-secondary/70 text-muted-foreground"><tr>{['Date','Firm','Action','Rating','Price Target'].map(label => <th key={label} className="px-4 py-3 text-left">{label}</th>)}</tr></thead><tbody>{ratings.map(item => <tr key={`${item.date}-${item.firm}`} className="border-t border-border"><td className="px-4 py-3 text-muted-foreground">{item.date}</td><td className="px-4 py-3 font-medium">{item.firm}</td><td className="px-4 py-3">{item.action}</td><td className={`px-4 py-3 font-semibold ${item.tone}`}>{item.rating}</td><td className="px-4 py-3 tabular-nums">{item.target}</td></tr>)}</tbody></table></div></div>
    </section>

    <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><h3 className="text-sm font-semibold">Earnings &amp; Revenue Estimates</h3><div className="mt-4 overflow-x-auto"><table className="w-full min-w-[480px] text-xs"><thead className="text-muted-foreground"><tr><th className="py-2 text-left">Estimate</th><th className="text-right">Current Qtr.</th><th className="text-right">Next Qtr.</th><th className="text-right">FY 2026</th></tr></thead><tbody>{[['Revenue','124.8B','98.4B','435.2B'],['EPS','2.35','1.72','7.42'],['YoY Growth','8.4%','6.1%','7.8%']].map(row => <tr key={row[0]} className="border-t border-border"><td className="py-3 font-medium">{row[0]}</td>{row.slice(1).map(value => <td key={value} className="text-right tabular-nums">{value}</td>)}</tr>)}</tbody></table></div></div>
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><h3 className="text-sm font-semibold">Technical Snapshot</h3><div className="mt-4 grid grid-cols-2 gap-x-6">{[['RSI (14)','58.4','Neutral'],['50-day MA','$221.35','Above'],['200-day MA','$204.18','Above'],['Volatility (30D)','21.8%','Moderate'],['Support','$218.40','Near'],['Resistance','$237.50','Watch']].map(([label,value,status]) => <div key={label} className="border-b border-border py-3 text-xs"><div className="text-muted-foreground">{label}</div><div className="mt-1 flex justify-between"><b>{value}</b><span className="text-primary">{status}</span></div></div>)}</div></div>
    </section>
    </>}

    {section === 'News & Filings' && <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.35fr_.65fr]">
      <section className="overflow-hidden rounded-lg border border-border bg-card shadow-sm"><div className="border-b border-border p-4"><h3 className="text-sm font-semibold">News &amp; Regulatory Filings</h3><p className="mt-0.5 text-xs text-muted-foreground">Sample headlines · SEC/DART integration pending</p></div>{news.map(item => <button key={item.title} className="flex w-full items-start gap-4 border-b border-border p-4 text-left last:border-0 hover:bg-secondary/50"><span className={`mt-0.5 rounded px-2 py-1 text-[10px] font-semibold ${item.tag === 'Filing' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/30 dark:text-amber-300':'bg-primary/10 text-primary'}`}>{item.tag}</span><span className="flex-1"><span className="block text-sm font-medium">{item.title}</span><span className="mt-1 block text-xs text-muted-foreground">{item.source} · {item.time}</span></span><ExternalLink size={14} className="mt-1 text-muted-foreground"/></button>)}</section>
      <div className="space-y-4"><section className="rounded-lg border border-border bg-card p-4 shadow-sm"><div className="flex items-center gap-2"><CalendarDays size={16} className="text-primary"/><h3 className="text-sm font-semibold">Upcoming Events</h3></div><div className="mt-4 space-y-4">{events.map(row => <div key={row[0]} className="border-l-2 border-primary pl-3"><div className="text-xs font-semibold">{row[1]}</div><div className="mt-1 text-xs text-muted-foreground">{row[0]} · {row[2]}</div></div>)}</div></section><section className="rounded-lg border border-border bg-card p-4 text-xs shadow-sm"><h3 className="text-sm font-semibold">Data Coverage</h3><div className="mt-3 space-y-2 text-muted-foreground"><p>Price: sample · delayed</p><p>Financials: sample annual values</p><p>Filings: SEC/DART connector pending</p><p>Updated: Nov 21, 2026 15:30 KST</p></div></section></div>
    </div>}
  </div>;
}
