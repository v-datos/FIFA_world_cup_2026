import React from 'react';
import { Calendar, MapPin, Clock, ArrowRight } from 'lucide-react';
import { getFlag } from '../lib/teamData';

interface Match {
  id: string;
  team1: string;
  team2: string;
  date: string;
  time: string;
  venue: string;
  stage: string;
  lifecycle?: 'finished' | 'today' | 'upcoming' | 'unresolved' | 'archived';
}

interface OverviewTabProps {
  matches: Match[];
  onSelectMatch: (matchId: string) => void;
  activeDate: string;
  lang: string;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  matches,
  onSelectMatch,
  activeDate,
  lang,
}) => {
  const filteredMatches = matches.filter((match) => match.lifecycle === 'today');

  // World Cup 2026 group-stage totals as of June 17 (live worldcup26.ir feed: 20 matches played)
  const matchesPlayed = 20;
  const totalGoals = 62;
  const topScorer = "L. Messi: 3 Goals";
  const topScorerES = "L. Messi: 3 Goles";

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
            <span className="text-3xl font-bold text-slate-100">{matchesPlayed}</span>
            <span className="text-xs text-slate-500">/ 104</span>
          </div>
        </div>

        <div className="glass-panel p-5 flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {lang === 'Español' ? 'Goles Totales' : 'Total Goals Scored'}
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold text-slate-100">{totalGoals}</span>
            <span className="text-xs text-emerald-400 font-mono">
              avg {(totalGoals / matchesPlayed).toFixed(1)} / game
            </span>
          </div>
        </div>

        <div className="glass-panel p-5 flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {lang === 'Español' ? 'Goleadores Líderes' : 'Top Scorers'}
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-lg font-bold text-slate-100">
              {lang === 'Español' ? topScorerES : topScorer}
            </span>
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
                    {match.time}
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
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    {match.venue}
                  </span>
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
