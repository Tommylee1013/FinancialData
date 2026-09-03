import { Sun, Moon, BarChart2, Activity, Globe, TrendingUp, Package, Factory, PieChart, Bot, Landmark, CircleDollarSign } from "lucide-react";

type Tab = 'home' | 'market' | 'foreign-exchange' | 'fixed-income' | 'fedwatch' | 'supply-chain' | 'macro' | 'commodities' | 'industry' | 'asset-allocation' | 'ai-research';

interface NavBarProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  isDark: boolean;
  toggleDark: () => void;
}

const navItems: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'home',             label: 'Overview',      icon: <BarChart2 size={13} /> },
  { id: 'market',           label: 'Market',         icon: <Activity  size={13} /> },
  { id: 'foreign-exchange', label: 'FX',             icon: <CircleDollarSign size={13} /> },
  { id: 'fixed-income',     label: 'Fixed Income',   icon: <TrendingUp size={13} /> },
  { id: 'fedwatch',         label: 'FedWatch',        icon: <Landmark size={13} /> },
  { id: 'supply-chain',     label: 'Supply Chain',   icon: <Globe     size={13} /> },
  { id: 'macro',            label: 'Macro',          icon: <BarChart2 size={13} /> },
  { id: 'commodities',      label: 'Commodities',    icon: <Package   size={13} /> },
  { id: 'industry',         label: 'Industry',       icon: <Factory   size={13} /> },
  { id: 'asset-allocation', label: 'Asset Alloc.',   icon: <PieChart  size={13} /> },
  { id: 'ai-research',      label: 'AI Research',    icon: <Bot size={13} /> },
];

export function NavBar({ activeTab, setActiveTab, isDark, toggleDark }: NavBarProps) {
  return (
    <header className="sticky top-0 z-50 bg-card border-b border-border shadow-sm">
      <div className="flex items-center h-12 px-4 gap-6">
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
            <BarChart2 size={14} className="text-primary-foreground" />
          </div>
          <span className="text-sm font-bold tracking-widest text-foreground" style={{ fontFamily: 'Roboto Condensed, sans-serif', letterSpacing: '0.1em' }}>
            FINDASH
          </span>
          <span className="text-xs text-muted-foreground ml-1 hidden sm:block">PRO</span>
        </div>

        <div className="w-px h-6 bg-border" />

        <nav className="flex items-center gap-0.5 overflow-x-auto">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-all
                ${activeTab === item.id
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
                }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden md:flex items-center gap-1.5 text-xs text-muted-foreground">
            <div className="w-1.5 h-1.5 rounded-full bg-up animate-pulse" />
            <span>LIVE</span>
          </div>
          <div className="text-xs text-muted-foreground font-mono hidden md:block">
            {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </div>
          <button
            onClick={toggleDark}
            className="p-1.5 rounded hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
          >
            {isDark ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>
      </div>
    </header>
  );
}

export type { Tab };
