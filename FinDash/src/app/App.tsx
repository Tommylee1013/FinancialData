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
import { dashboardConnection, marketIndices, commodities, freightIndices, volatilityIndices } from "./data/mockData";
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
  const selected = [marketIndices[0], marketIndices[3], marketIndices[5], freightIndices[0],
    commodities[0], commodities[3], volatilityIndices[0]].filter(Boolean);
  const items = selected.map(item =>
    `${item.name}  ${item.value.toLocaleString('en-US', { maximumFractionDigits: 2 })}  ${item.changePct >= 0 ? '+' : ''}${item.changePct.toFixed(2)}%`
  );
  const doubled = [...items, ...items];

  return (
    <div className="bg-primary text-primary-foreground overflow-hidden h-6 flex items-center text-[10px] font-mono">
      <div
        className="whitespace-nowrap flex gap-8 animate-marquee"
        style={{ animation: 'marquee 40s linear infinite' }}
      >
        {doubled.map((item, i) => {
          const isNeg = item.includes('-') && !item.includes('-%');
          const isPos = item.match(/\+\d/);
          const color = isNeg ? '#FCA5A5' : isPos ? '#86EFAC' : 'inherit';
          return (
            <span key={i} style={{ color }}>
              {item}
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
