import React, { useState } from 'react';
import { LayoutDashboard, Swords, Trophy, ChevronLeft, ChevronRight } from 'lucide-react';
import ballLogo from '../assets/ball-logo.png';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  lang: string;
  setLang: (lang: string) => void;
}

// Sidebar brand icon uses the official FIFA World Cup 26 match-ball logo asset.

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  lang,
  setLang,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { id: 'overview', label: lang === 'Español' ? 'Vista General' : 'Overview', icon: LayoutDashboard },
    { id: 'matches', label: lang === 'Español' ? 'Análisis Partidos' : 'Match Analysis', icon: Swords },
    { id: 'standings', label: lang === 'Español' ? 'Tabla y Llaves' : 'Standings & Bracket', icon: Trophy },
  ];

  return (
    <aside className={`${collapsed ? 'w-20' : 'w-64'} min-h-screen bg-slate-950/40 border-r border-slate-800/60 flex flex-col backdrop-blur-xl z-20 transition-[width] duration-200 ease-in-out`}>
      {/* Brand Header */}
      <div className={`border-b border-slate-800/60 ${collapsed ? 'p-3 flex flex-col items-center gap-2' : 'p-4 flex items-center justify-between gap-3'}`}>
        <div className={`flex items-center min-w-0 ${collapsed ? '' : 'gap-3'}`}>
          <img src={ballLogo} alt="FIFA World Cup 26 official match ball" className="w-10 h-10 rounded-full object-cover shrink-0 border border-slate-700/60" />
          {!collapsed && (
            <div className="min-w-0">
              <h1 className="text-sm font-bold text-slate-100 uppercase tracking-wider leading-tight truncate">
                FIFA 2026
              </h1>
              <p className="text-[10px] text-slate-500 font-medium tracking-widest uppercase">
                {lang === 'Español' ? 'Copa Mundial' : 'World Cup'}
              </p>
            </div>
          )}
        </div>
        <button
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? (lang === 'Español' ? 'Expandir' : 'Expand') : (lang === 'Español' ? 'Contraer' : 'Collapse')}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-900/40 transition-all shrink-0"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className={`flex-1 py-6 space-y-1.5 ${collapsed ? 'px-2' : 'px-4'}`}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center rounded-xl text-sm font-medium transition-all duration-200 ${
                collapsed ? 'justify-center py-3' : 'gap-3.5 px-4.5 py-3.5'
              } ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-lg shadow-emerald-500/5'
                  : 'text-slate-400 hover:bg-slate-900/40 hover:text-slate-200 border border-transparent'
              }`}
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}

        {/* Language toggle — placed below Standings & Bracket ('Tabla y Llaves') */}
        {collapsed ? (
          <div className="flex flex-col items-center gap-1 mt-6 border-t border-slate-800/60 pt-4">
            <button 
              onClick={() => setLang(lang === 'English' ? 'Español' : 'English')} 
              title={lang === 'Español' ? 'Switch to English' : 'Cambiar a Español'}
              className="text-xs font-bold text-slate-400 hover:text-slate-200 uppercase bg-slate-900/40 p-2 rounded-lg border border-slate-800/60 transition-all duration-150"
            >
              {lang === 'English' ? 'ES' : 'EN'}
            </button>
          </div>
        ) : (
          <div className="mt-6 border-t border-slate-800/60 pt-4 px-1.5">
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              {lang === 'Español' ? 'Idioma' : 'Language'}
            </div>
            <div className="flex items-center gap-1 p-1 bg-slate-900/80 backdrop-blur rounded-lg border border-slate-800/60 shadow-lg">
              <button
                onClick={() => setLang('English')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all duration-150 ${
                  lang === 'English' ? 'bg-emerald-500/15 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLang('Español')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all duration-150 ${
                  lang === 'Español' ? 'bg-emerald-500/15 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Español
              </button>
            </div>
          </div>
        )}
      </nav>

    </aside>
  );
};
