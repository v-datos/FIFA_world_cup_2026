import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { OverviewTab } from './components/OverviewTab';
import { MatchAnalysisTab } from './components/MatchAnalysisTab';
import { StandingsTab } from './components/StandingsTab';
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
  const [lang, setLang] = useState<string>('English');
  const [matches, setMatches] = useState<Match[]>([]);
  const [activeDate, setActiveDate] = useState<string>('');
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

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
  };

  return (
    <div className="flex min-h-screen bg-[#070a13] text-slate-100 font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        lang={lang}
        setLang={setLang}
      />

      {/* Main Content Pane */}
      <main className="flex-1 min-h-screen overflow-y-auto p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
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
