import React, { useState, useEffect } from 'react';
import { Calendar, MapPin, Clock, ArrowRight } from 'lucide-react';
import { getFlag } from '../lib/teamData';

interface Match {
  id: string;
  team1: string;
  team2: string;
  date: string;
  time: string;
  kickoff_utc?: string | null;
  venue: string;
  stage: string;
  lifecycle?: 'finished' | 'today' | 'upcoming' | 'unresolved' | 'archived';
}

// Kickoffs are shown in Edmonton, Alberta (Mountain) time. When a UTC kickoff is
// available we convert it; otherwise we fall back to the stored local string.
const EDMONTON_TZ = 'America/Edmonton';
const edmontonTime = (match: Match): string => {
  if (match.kickoff_utc) {
    const d = new Date(match.kickoff_utc);
    if (!isNaN(d.getTime())) {
      return new Intl.DateTimeFormat('en-CA', {
        timeZone: EDMONTON_TZ,
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }).format(d) + ' MT';
    }
  }
  return match.time || 'TBD';
};

const mapsUrl = (venue: string): string =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(venue)}`;

interface Scorer {
  name: string;
  team?: string;
  goals: number;
}

interface TournamentStats {
  matches_played: number;
  total_matches: number;
  total_goals: number;
  goals_per_game: number | null;
  top_scorer: Scorer[] | Scorer | null;
}

interface OverviewTabProps {
  matches: Match[];
  onSelectMatch: (matchId: string) => void;
  activeDate: string;
  lang: string;
  serverUrl: string;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  matches,
  onSelectMatch,
  activeDate,
  lang,
  serverUrl,
}) => {
  const filteredMatches = matches.filter((match) => match.lifecycle === 'today');

  // Tournament totals are derived live from /api/standings (same source as the
  // bracket): matches played and goals come from the live group standings; the
  // top scorer is a curated grid_state.json field surfaced through that payload.
  const [stats, setStats] = useState<TournamentStats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${serverUrl}/api/standings`);
        if (res.ok) {
          const json = await res.json();
          if (json.tournament_stats) setStats(json.tournament_stats);
        }
      } catch (err) {
        console.error('Error fetching tournament stats', err);
      }
    };
    fetchStats();
  }, [serverUrl]);

  const totalMatches = stats?.total_matches ?? 104;
  const matchesPlayed = stats ? stats.matches_played : null;
  const totalGoals = stats ? stats.total_goals : null;
  const goalsPerGame = stats?.goals_per_game ?? null;
  const scorer = stats?.top_scorer ?? null;
  const goalsLabel = lang === 'Español' ? 'Goles' : 'Goals';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-100">
          {lang === 'Español' ? 'Panel de Control del Mundial 2026' : 'FIFA World Cup 2026 Dashboard'}
        </h2>
        <p className="text-sm text-slate-400">
          {lang === 'Español' ? 'Seguimiento en vivo, predicciones y análisis táctico' : 'Live tracking, tactical forecasts, and match event timelines'}
        </p>
      </div>

      {/* Tournament Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-panel p-5 flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {lang === 'Español' ? 'Partidos Jugados' : 'Matches Played'}
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold text-slate-100">{matchesPlayed ?? '—'}</span>
            <span className="text-xs text-slate-500">/ {totalMatches}</span>
          </div>
        </div>

        <div className="glass-panel p-5 flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {lang === 'Español' ? 'Goles Totales' : 'Total Goals Scored'}
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold text-slate-100">{totalGoals ?? '—'}</span>
            {goalsPerGame !== null && (
              <span className="text-xs text-emerald-400 font-mono">
                avg {goalsPerGame.toFixed(1)} / game
              </span>
            )}
          </div>
        </div>

        <div className="glass-panel p-5 flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {lang === 'Español' ? 'Goleadores Líderes' : 'Top Scorers'}
          </span>
          <div className="flex flex-col gap-1.5 mt-2 justify-center flex-grow">
            {scorer ? (
              Array.isArray(scorer) ? (
                scorer.map((s, idx) => (
                  <div key={idx} className="flex items-center gap-1.5">
                    <span className="text-lg">{s.team ? getFlag(s.team) : ''}</span>
                    <span className="text-sm font-bold text-slate-100">
                      {s.name} <span className="text-xs text-slate-400">({s.goals} {goalsLabel})</span>
                    </span>
                  </div>
                ))
              ) : (
                <div className="flex items-center gap-1.5">
                  <span className="text-lg">{(scorer as Scorer).team ? getFlag((scorer as Scorer).team!) : ''}</span>
                  <span className="text-sm font-bold text-slate-100">
                    {(scorer as Scorer).name} <span className="text-xs text-slate-400">({(scorer as Scorer).goals} {goalsLabel})</span>
                  </span>
                </div>
              )
            ) : (
              <span className="text-lg font-bold text-slate-100">—</span>
            )}
          </div>
        </div>
      </div>

      {/* Matches Grid */}
      <div className="glass-panel p-6">
        <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-emerald-400" />
          <span>
            {lang === 'Español'
              ? `Partidos del Día (${activeDate || 'hoy'})`
              : `Fixtures of the Day (${activeDate || 'today'})`}
          </span>
        </h3>

        {filteredMatches.length === 0 ? (
          <div className="border border-slate-800/60 rounded-lg px-4 py-6 text-sm text-slate-400">
            {lang === 'Español'
              ? 'No hay partidos activos pendientes para el día.'
              : 'No active unfinished fixtures for the day.'}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredMatches.map((match) => (
              <div
                key={match.id}
                onClick={() => onSelectMatch(match.id)}
                className="glass-panel p-4 glass-panel-hover flex flex-col justify-between cursor-pointer group"
              >
                {/* Stage Header */}
                <div className="flex justify-between items-center mb-3">
                  <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {match.stage}
                  </span>
                  <span className="text-[10px] text-slate-500 flex items-center gap-1 font-mono">
                    <Clock className="w-3 h-3" />
                    {edmontonTime(match)}
                  </span>
                </div>

                {/* Matchup */}
                <div className="flex justify-between items-center my-2 px-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getFlag(match.team1)}</span>
                    <span className="text-base font-bold text-slate-100 group-hover:text-emerald-400 transition-colors duration-150">
                      {match.team1}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-500">VS</span>
                  <div className="flex items-center gap-2 flex-row-reverse">
                    <span className="text-xl">{getFlag(match.team2)}</span>
                    <span className="text-base font-bold text-slate-100 group-hover:text-emerald-400 transition-colors duration-150 text-right">
                      {match.team2}
                    </span>
                  </div>
                </div>

                {/* Venue / Footer */}
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-800/40 text-[11px] text-slate-400">
                  <a
                    href={mapsUrl(match.venue)}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-1 hover:text-emerald-400 hover:underline transition-colors"
                    title={lang === 'Español' ? 'Ver en Google Maps' : 'View on Google Maps'}
                  >
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    {match.venue}
                  </a>
                  <span className="flex items-center gap-0.5 text-emerald-400 group-hover:translate-x-1 transition-transform duration-200">
                    {lang === 'Español' ? 'Analizar' : 'Analyze'}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
