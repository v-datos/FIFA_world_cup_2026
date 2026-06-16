import React from 'react';
import { LayoutDashboard, Swords, Trophy, Languages } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  lang: string;
  setLang: (lang: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  lang,
  setLang,
}) => {
  const menuItems = [
    { id: 'overview', label: lang === 'Español' ? 'Vista General' : 'Overview', icon: LayoutDashboard },
    { id: 'matches', label: lang === 'Español' ? 'Análisis Partidos' : 'Match Analysis', icon: Swords },
    { id: 'standings', label: lang === 'Español' ? 'Tabla y Llaves' : 'Standings & Bracket', icon: Trophy },
  ];

  return (
    <aside className="w-64 min-h-screen bg-slate-950/40 border-r border-slate-800/60 flex flex-col backdrop-blur-xl z-20">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800/60 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center font-bold text-emerald-400 text-lg font-mono">
          🏟️
        </div>
        <div>
          <h1 className="text-sm font-bold text-slate-100 uppercase tracking-wider leading-tight">
            FIFA 2026
          </h1>
          <p className="text-[10px] text-slate-500 font-medium tracking-widest uppercase">
            {lang === 'Español' ? 'Panel Analítico' : 'Analytics Board'}
          </p>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 px-4 py-6 space-y-1.5">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3.5 px-4.5 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-lg shadow-emerald-500/5'
                  : 'text-slate-400 hover:bg-slate-900/40 hover:text-slate-200 border border-transparent'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Language Switcher Footer */}
      <div className="p-4 border-t border-slate-800/60">
        <div className="glass-panel p-3.5 flex flex-col gap-2.5">
          <div className="flex items-center gap-2 text-[11px] text-slate-400 uppercase tracking-widest font-mono">
            <Languages className="w-4 h-4 text-emerald-400" />
            <span>Language / Idioma</span>
          </div>
          <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-900/60 rounded-lg border border-slate-800/40">
            <button
              onClick={() => setLang('English')}
              className={`py-1.5 text-xs font-semibold rounded-md transition-all duration-150 ${
                lang === 'English'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => setLang('Español')}
              className={`py-1.5 text-xs font-semibold rounded-md transition-all duration-150 ${
                lang === 'Español'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ES
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};
