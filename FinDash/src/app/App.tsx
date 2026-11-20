import React, { useState, useEffect } from "react";
import { NavBar, type Tab } from "./components/NavBar";
import { MainDashboard } from "./components/MainDashboard";
import { MarketTab } from "./components/tabs/MarketTab";
import { FixedIncomeTab } from "./components/tabs/FixedIncomeTab";
import { SupplyChainTab } from "./components/tabs/SupplyChainTab";
import { MacroEconomicsTab } from "./components/tabs/MacroEconomicsTab";
import { CommoditiesTab } from "./components/tabs/CommoditiesTab";
import { IndustryTab } from "./components/tabs/IndustryTab";
import { AssetAllocationTab } from "./components/tabs/AssetAllocationTab";
import { AIResearchTab } from "./components/tabs/AIResearchTab";
import { FedWatchTab } from "./components/tabs/FedWatchTab";
import { ForeignExchangeTab } from "./components/tabs/ForeignExchangeTab";
import { StocksTab } from "./components/tabs/StocksTab";
import { StructuralBreaksTab } from "./components/tabs/StructuralBreaksTab";
import { dashboardConnection, tickerTape } from "./data/mockData";
import { DetailPage } from "./components/DetailPage";
import { readDetailRoute } from "./detailNavigation";
import { Bell, CalendarDays, Database, Menu, Search } from "lucide-react";

const TAB_LABELS: Record<Tab, string> = {
  home:               'Overview — Global Market Summary',
  market:             'Market — Indices · Sectors · Sentiment',
  'foreign-exchange': 'Foreign Exchange — Global Currencies · FX Indices',
  'fixed-income':     'Fixed Income — Yield Curves · Swaps',
  fedwatch:           'FedWatch — FOMC Decision Probabilities',
  stocks:             'Stocks — Prices · Financials · Analyst Ratings',
  'supply-chain':     'Supply Chain — Freight Indices · Ports',
  macro:              'Macro Economics — Economic Indicators',
  commodities:        'Commodities — Raw Materials & Goods',
  industry:           'Industry — Semiconductors · Real Estate · Energy',
  'asset-allocation': 'Asset Allocation — Portfolio Optimization',
  'structural-breaks': 'Structural Breaks — Regime Detection · Model Ensemble',
  'ai-research':      'AI Research — Financial Data Agent',
};

function TickerBar() {
  const doubled = [...tickerTape, ...tickerTape];

  return (
    <div className="bg-primary text-primary-foreground overflow-hidden h-8 flex items-center text-[11px] tabular-nums border-b border-white/10">
      <div
        className="whitespace-nowrap flex gap-7 animate-marquee hover:[animation-play-state:paused]"
        style={{ animation: 'marquee 125s linear infinite' }}
      >
        {doubled.map((item, i) => {
          const isNeg = item.changePct != null && item.changePct < 0;
          const isPos = item.changePct != null && item.changePct > 0;
          const color = isNeg ? '#FCA5A5' : isPos ? '#86EFAC' : item.connected ? 'inherit' : '#BFDBFE';
          const value = item.value == null ? 'N/A' : item.value.toLocaleString('en-US', { maximumFractionDigits: item.category === 'Rates' ? 3 : 2 });
          const change = item.changePct == null ? '' : `  ${item.changePct >= 0 ? '+' : ''}${item.changePct.toFixed(2)}%`;
          return (
            <span key={`${item.id}-${i}`} style={{ color }} className="inline-flex items-center gap-1.5">
              <span className="text-[8px] tracking-wide text-blue-200/70">{item.category.toUpperCase()}</span>
              <span className="font-semibold">{item.name}</span>
              <span>{value}{change}</span>
            </span>
          );
        })}
      </div>
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('home');
  const [isDark, setIsDark] = useState(false);
  const [detail, setDetail] = useState(readDetailRoute());
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('findash-theme');
    if (saved === 'dark') {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  useEffect(() => {
    const onHashChange = () => setDetail(readDetailRoute());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const toggleDark = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('findash-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('findash-theme', 'light');
    }
  };

  const changeTab = (tab: Tab) => {
    if (window.location.hash) window.location.hash = '';
    setActiveTab(tab);
  };

  const [pageTitle, pageSubtitle] = (detail ? 'Instrument Detail — Historical data & research context' : TAB_LABELS[activeTab]).split(' — ');
  const sectionLabel = activeTab === 'home' || activeTab === 'fedwatch' || activeTab === 'stocks'
    ? 'Dashboard'
    : activeTab === 'asset-allocation' || activeTab === 'structural-breaks' || activeTab === 'ai-research'
      ? 'Tools'
      : 'Research';

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <NavBar activeTab={activeTab} setActiveTab={changeTab} isDark={isDark} toggleDark={toggleDark} mobileOpen={mobileNavOpen} onMobileClose={() => setMobileNavOpen(false)} />

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">
          <div className="flex h-16 items-center gap-3 px-4 sm:px-6">
            <button onClick={() => setMobileNavOpen(true)} className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-secondary hover:text-foreground lg:hidden" aria-label="Open navigation"><Menu size={18} /></button>
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.13em] text-muted-foreground"><span>FinDash</span><span>/</span><span>{sectionLabel}</span></div>
              <h1 className="truncate text-base font-semibold leading-6 text-foreground sm:text-lg">{pageTitle}</h1>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <button onClick={() => changeTab('ai-research')} className="hidden h-9 w-52 items-center gap-2 rounded-lg border border-border bg-background px-3 text-left text-xs text-muted-foreground shadow-sm transition-colors hover:bg-secondary md:flex"><Search size={14} /><span className="flex-1">Ask financial data</span><span className="rounded border border-border px-1.5 py-0.5 text-[9px]">AI</span></button>
              <button className="hidden items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-[11px] text-muted-foreground shadow-sm xl:flex" aria-label="Current date"><CalendarDays size={14} /><span>{new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span></button>
              <button className="relative rounded-lg border border-border bg-background p-2 text-muted-foreground shadow-sm hover:bg-secondary hover:text-foreground" aria-label="Notifications"><Bell size={16} /><span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary" /></button>
            </div>
          </div>
          <div className="flex min-h-9 items-center justify-between border-t border-border/70 px-4 py-1.5 sm:px-6">
            <p className="truncate text-[11px] text-muted-foreground">{pageSubtitle}</p>
            <div className="ml-4 hidden shrink-0 items-center gap-1.5 text-[10px] font-medium text-muted-foreground sm:flex"><Database size={12} /><span>{dashboardConnection.connected ? 'Live workspace' : 'Demo workspace'}</span></div>
          </div>
        </header>

        <TickerBar />
        <main className="min-h-0 flex-1 overflow-auto">
          {detail ? <DetailPage kind={detail.kind} id={detail.id} onBack={() => { history.back(); }} onAskAI={(context) => { localStorage.setItem('findash-ai-context', JSON.stringify(context)); window.location.hash = ''; setActiveTab('ai-research'); }} /> : <>
          {activeTab === 'home' && <MainDashboard setActiveTab={changeTab} />}
          {activeTab === 'market' && <MarketTab />}
          {activeTab === 'foreign-exchange' && <ForeignExchangeTab />}
          {activeTab === 'fixed-income' && <FixedIncomeTab />}
          {activeTab === 'fedwatch' && <FedWatchTab />}
          {activeTab === 'stocks' && <StocksTab />}
          {activeTab === 'supply-chain' && <SupplyChainTab />}
          {activeTab === 'macro' && <MacroEconomicsTab />}
          {activeTab === 'commodities' && <CommoditiesTab />}
          {activeTab === 'industry' && <IndustryTab />}
          {activeTab === 'asset-allocation' && <AssetAllocationTab />}
          {activeTab === 'structural-breaks' && <StructuralBreaksTab />}
          {activeTab === 'ai-research' && <AIResearchTab />}
          </>}
        </main>
        <footer className="flex flex-col gap-1 border-t border-border bg-card px-4 py-2.5 text-[10px] text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span>FINDASH · Personal financial intelligence workspace</span>
          <span className="font-mono">{dashboardConnection.connected ? '● DuckDB live' : '○ Demo fallback'} · {dashboardConnection.updatedAt ? new Date(dashboardConnection.updatedAt).toLocaleString() : 'API not connected'} · Not investment advice</span>
        </footer>
      </div>
    </div>
  );
}
