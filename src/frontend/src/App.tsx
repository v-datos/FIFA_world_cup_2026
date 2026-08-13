import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { OverviewTab } from './components/OverviewTab';
import { MatchAnalysisTab } from './components/MatchAnalysisTab';
import { StandingsTab } from './components/StandingsTab';
import { Menu, Archive } from 'lucide-react';
import './App.css';

interface Match {
  id: string;
  team1: string;
  team2: string;
  date: string;
  time: string;
  venue: string;
  stage: string;
  lifecycle?: 'finished' | 'today' | 'upcoming' | 'unresolved' | 'archived';
  source_status?: string;
  is_finished?: boolean;
  is_briefing_candidate?: boolean;
}

function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [lang, setLang] = useState<string>('Español');
  const [matches, setMatches] = useState<Match[]>([]);
  const [activeDate, setActiveDate] = useState<string>('');
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  // Dynamically resolve backend API server URL
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const serverUrl = isLocal 
    ? 'http://localhost:8080' 
    : 'https://fifa-2026-dashboard-80399171028.us-central1.run.app';

  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${serverUrl}/api/schedule`);
        if (res.ok) {
          const data = await res.json();
          const scheduleMatches = data.matches || [];
          const dayMatches = scheduleMatches.filter((match: Match) => match.lifecycle === 'today');
          setMatches(scheduleMatches);
          setActiveDate(data.active_date || dayMatches[0]?.date || '');
          setSelectedMatchId(data.default_match_id || dayMatches[0]?.id || null);
        }
      } catch (err) {
        console.error('Failed to load schedule from API server', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSchedule();
  }, [serverUrl]);

  const handleSelectMatch = (matchId: string) => {
    setSelectedMatchId(matchId);
    setActiveTab('matches');
    setIsMobileMenuOpen(false);
  };

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [activeTab]);

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-[#070a13] text-slate-100 font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Mobile Top Bar */}
      <div className="md:hidden sticky top-0 left-0 right-0 bg-[#070a13]/90 backdrop-blur border-b border-slate-800/60 p-4 flex items-center justify-between z-30">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="Open sidebar"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 transition-all"
          >
            <Menu className="w-6 h-6" />
          </button>
          <span className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            FIFA 2026
          </span>
        </div>
        <span className="text-[10px] text-slate-500 font-medium tracking-widest uppercase bg-slate-950/60 px-2 py-1 rounded border border-slate-800/60">
          {lang === 'Español' ? 'Mundial' : 'World Cup'}
        </span>
      </div>

      {/* Mobile Menu Backdrop */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-35 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        lang={lang}
        setLang={setLang}
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      {/* Main Content Pane */}
      <main className="flex-1 min-h-screen overflow-y-auto p-4 md:p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Archive / Retired Notice Banner */}
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-amber-200 shadow-lg backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-500/20 rounded-lg text-amber-400 shrink-0">
              <Archive className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-amber-300">
                {lang === 'Español' ? 'Proyecto Archivado — Mundial Concluido' : 'Project Archived — Tournament Complete'}
              </h4>
              <p className="text-xs text-amber-200/80 mt-0.5">
                {lang === 'Español' 
                  ? 'Este panel de control se encuentra archivado en modo de lectura con los resultados finales y datos históricos del torneo.'
                  : 'This dashboard is archived in read-only mode featuring final tournament results and historical analytics.'}
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider bg-amber-500/20 px-2.5 py-1 rounded border border-amber-500/40 text-amber-300 shrink-0">
            {lang === 'Español' ? 'Archivado' : 'Archived'}
          </span>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
            <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-semibold text-slate-400">
              {lang === 'Español' ? 'Cargando datos del torneo...' : 'Loading tournament center...'}
            </span>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <OverviewTab
                matches={matches}
                onSelectMatch={handleSelectMatch}
                activeDate={activeDate}
                lang={lang}
                serverUrl={serverUrl}
              />
            )}
            
            {activeTab === 'matches' && (
              <MatchAnalysisTab 
                matches={matches}
                selectedMatchId={selectedMatchId}
                setSelectedMatchId={setSelectedMatchId}
                activeDate={activeDate}
                lang={lang}
                serverUrl={serverUrl}
              />
            )}

            {activeTab === 'standings' && (
              <StandingsTab 
                serverUrl={serverUrl} 
                lang={lang} 
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
