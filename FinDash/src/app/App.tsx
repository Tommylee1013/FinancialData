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
import { dashboardConnection, tickerTape } from "./data/mockData";
import { DetailPage } from "./components/DetailPage";
import { readDetailRoute } from "./detailNavigation";

const TAB_LABELS: Record<Tab, string> = {
  home:               'Overview — Global Market Summary',
  market:             'Market — Indices · Sectors · Sentiment',
  'fixed-income':     'Fixed Income — Yield Curves · Swaps',
  'supply-chain':     'Supply Chain — Freight Indices · Ports',
  macro:              'Macro Economics — Economic Indicators',
  commodities:        'Commodities — Raw Materials & Goods',
  industry:           'Industry — Semiconductors · Real Estate · Energy',
  'asset-allocation': 'Asset Allocation — Portfolio Optimization',
};

function TickerBar() {
  const doubled = [...tickerTape, ...tickerTape];

  return (
    <div className="bg-primary text-primary-foreground overflow-hidden h-8 flex items-center text-[11px] font-mono border-b border-white/10">
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

function TabHeader({ tab }: { tab: Tab }) {
  if (tab === 'home') return null;
  return (
    <div className="bg-card border-b border-border px-4 py-2">
      <h1 className="text-xs font-semibold text-muted-foreground" style={{ fontFamily: 'Roboto Condensed, sans-serif' }}>
        {TAB_LABELS[tab]}
      </h1>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('home');
  const [isDark, setIsDark] = useState(false);
  const [detail, setDetail] = useState(readDetailRoute());

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

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      <TickerBar />
      <NavBar activeTab={activeTab} setActiveTab={changeTab} isDark={isDark} toggleDark={toggleDark} />
      <TabHeader tab={activeTab} />
      <main className="flex-1 overflow-auto">
        {detail ? <DetailPage kind={detail.kind} id={detail.id} onBack={() => { history.back(); }} /> : <>
        {activeTab === 'home' && <MainDashboard setActiveTab={changeTab} />}
        {activeTab === 'market' && <MarketTab />}
        {activeTab === 'fixed-income' && <FixedIncomeTab />}
        {activeTab === 'supply-chain' && <SupplyChainTab />}
        {activeTab === 'macro' && <MacroEconomicsTab />}
        {activeTab === 'commodities' && <CommoditiesTab />}
        {activeTab === 'industry' && <IndustryTab />}
        {activeTab === 'asset-allocation' && <AssetAllocationTab />}
        </>}
      </main>
      <footer className="border-t border-border px-4 py-2 flex items-center justify-between text-[10px] text-muted-foreground">
        <span>FINDASH PRO · Personal Finance Data Dashboard</span>
        <span className="font-mono">
          {dashboardConnection.connected ? '● DuckDB live' : '○ Demo fallback'} · {' '}
          {dashboardConnection.updatedAt ? new Date(dashboardConnection.updatedAt).toLocaleString() : 'API not connected'} ·
          {' '}Not for actual investment decisions
        </span>
      </footer>
    </div>
  );
}
