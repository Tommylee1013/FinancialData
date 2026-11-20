import type { ReactNode } from "react";
import {
  Activity, BarChart3, Bot, Boxes, ChevronRight, CircleDollarSign,
  Factory, Globe2, Landmark, LayoutDashboard, Moon, Package, LineChart,
  PanelLeftClose, PieChart, Sun, TrendingUp, X, ScanSearch,
} from "lucide-react";
import { dashboardConnection } from "../data/mockData";

type Tab = 'home' | 'stocks' | 'market' | 'foreign-exchange' | 'fixed-income' | 'fedwatch' | 'supply-chain' | 'macro' | 'commodities' | 'industry' | 'asset-allocation' | 'structural-breaks' | 'ai-research';

interface NavBarProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  isDark: boolean;
  toggleDark: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

type NavItem = { id: Tab; label: string; description: string; icon: ReactNode };

const groups: { label: string; items: NavItem[] }[] = [
  { label: '', items: [
    { id: 'home', label: 'Overview', description: 'Global dashboard', icon: <LayoutDashboard size={17} /> },
    { id: 'fedwatch', label: 'FedWatch', description: 'FOMC probabilities', icon: <Landmark size={17} /> },
    { id: 'stocks', label: 'Stocks', description: 'Prices & fundamentals', icon: <LineChart size={17} /> },
  ]},
  { label: 'Research', items: [
    { id: 'market', label: 'Market', description: 'Indices & sentiment', icon: <Activity size={17} /> },
    { id: 'foreign-exchange', label: 'Foreign Exchange', description: 'Currencies & FX', icon: <CircleDollarSign size={17} /> },
    { id: 'fixed-income', label: 'Fixed Income', description: 'Yields & swaps', icon: <TrendingUp size={17} /> },
    { id: 'supply-chain', label: 'Supply Chain', description: 'Freight & logistics', icon: <Globe2 size={17} /> },
    { id: 'macro', label: 'Macro Economics', description: 'Global indicators', icon: <BarChart3 size={17} /> },
    { id: 'commodities', label: 'Commodities', description: 'Raw materials', icon: <Package size={17} /> },
    { id: 'industry', label: 'Industry', description: 'Sector intelligence', icon: <Factory size={17} /> },
  ]},
  { label: 'Tools', items: [
    { id: 'asset-allocation', label: 'Asset Allocation', description: 'Portfolio optimizer', icon: <PieChart size={17} /> },
    { id: 'structural-breaks', label: 'Structural Breaks', description: 'Regime diagnostics', icon: <ScanSearch size={17} /> },
    { id: 'ai-research', label: 'AI Research', description: 'Financial agent', icon: <Bot size={17} /> },
  ]},
];

export function NavBar({ activeTab, setActiveTab, isDark, toggleDark, mobileOpen, onMobileClose }: NavBarProps) {
  const selectTab = (tab: Tab) => {
    setActiveTab(tab);
    onMobileClose();
  };

  return <>
    {mobileOpen && <button aria-label="Close navigation" className="fixed inset-0 z-40 bg-black/45 backdrop-blur-[1px] lg:hidden" onClick={onMobileClose} />}
    <aside className={`fixed inset-y-0 left-0 z-50 flex h-screen w-[248px] flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground shadow-xl transition-transform duration-200 lg:sticky lg:top-0 lg:z-30 lg:translate-x-0 lg:shadow-none ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex h-16 items-center border-b border-sidebar-border px-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm shadow-primary/20"><BarChart3 size={19} /></div>
        <div className="ml-3 min-w-0">
          <div className="text-sm font-bold tracking-[0.16em]">FINDASH</div>
          <div className="text-[11px] text-muted-foreground">Financial intelligence</div>
        </div>
        <button onClick={onMobileClose} className="ml-auto rounded-md p-2 text-muted-foreground hover:bg-sidebar-accent hover:text-foreground lg:hidden" aria-label="Close sidebar"><X size={17} /></button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        {groups.map((group, groupIndex) => <div key={group.label || 'primary'} className={groupIndex ? 'mt-5' : ''}>
          {group.label && <div className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{group.label}</div>}
          <nav className="space-y-1">
            {group.items.map(item => {
              const selected = activeTab === item.id;
              return <button key={item.id} onClick={() => selectTab(item.id)} className={`group flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left transition-colors ${selected ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'}`}>
                <span className={selected ? 'text-white' : 'text-muted-foreground group-hover:text-foreground'}>{item.icon}</span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[13px] font-semibold leading-4">{item.label}</span>
                  <span className={`block truncate text-[10px] leading-4 ${selected ? 'text-white/65' : 'text-muted-foreground'}`}>{item.description}</span>
                </span>
                <ChevronRight size={13} className={selected ? 'opacity-70' : 'opacity-0 transition-opacity group-hover:opacity-50'} />
              </button>;
            })}
          </nav>
        </div>)}
      </div>

      <div className="border-t border-sidebar-border p-3">
        <div className="mb-2 flex items-center justify-between rounded-lg border border-sidebar-border bg-background/55 px-3 py-2.5">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className={`h-2 w-2 shrink-0 rounded-full ${dashboardConnection.connected ? 'bg-up shadow-[0_0_0_3px_rgba(22,163,74,0.12)]' : 'bg-amber-500'}`} />
            <div className="min-w-0"><div className="text-[11px] font-semibold">{dashboardConnection.connected ? 'DuckDB connected' : 'Demo fallback'}</div><div className="truncate text-[9px] text-muted-foreground">Local data service</div></div>
          </div>
          <Boxes size={14} className="text-muted-foreground" />
        </div>
        <button onClick={toggleDark} className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-sidebar-accent hover:text-foreground">
          {isDark ? <Sun size={16} /> : <Moon size={16} />}<span>{isDark ? 'Light appearance' : 'Dark appearance'}</span><PanelLeftClose size={14} className="ml-auto opacity-40" />
        </button>
      </div>
    </aside>
  </>;
}

export type { Tab };
