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
  const items = [
    'S&P 500  5,234.18  +0.83%',
    'KOSPI  2,743.82  -0.23%',
    'Nikkei 225  38,236.07  +0.92%',
    'BDI  1,842  +1.27%',
    'WTI  $78.23  +1.12%',
    'Gold  $2,341.50  +0.53%',
    'US 10Y  4.25%  -6bp',
    'EURUSD  1.0843  +0.12%',
    'USDJPY  156.34  -0.23%',
    'USDKRW  1,384.5  +0.08%',
    'VIX  13.42  -6.09%',
    'SCFI  2,456  -1.80%',
  ];
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

  useEffect(() => {
    const saved = localStorage.getItem('findash-theme');
    if (saved === 'dark') {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }
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

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      <TickerBar />
      <NavBar activeTab={activeTab} setActiveTab={setActiveTab} isDark={isDark} toggleDark={toggleDark} />
      <TabHeader tab={activeTab} />
      <main className="flex-1 overflow-auto">
        {activeTab === 'home' && <MainDashboard setActiveTab={setActiveTab} />}
        {activeTab === 'market' && <MarketTab />}
        {activeTab === 'fixed-income' && <FixedIncomeTab />}
        {activeTab === 'supply-chain' && <SupplyChainTab />}
        {activeTab === 'macro' && <MacroEconomicsTab />}
        {activeTab === 'commodities' && <CommoditiesTab />}
        {activeTab === 'industry' && <IndustryTab />}
        {activeTab === 'asset-allocation' && <AssetAllocationTab />}
      </main>
      <footer className="border-t border-border px-4 py-2 flex items-center justify-between text-[10px] text-muted-foreground">
        <span>FINDASH PRO · Personal Finance Data Dashboard</span>
        <span className="font-mono">
          {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })} ·
          Simulated data only · Not for actual investment decisions
        </span>
      </footer>
    </div>
  );
}
