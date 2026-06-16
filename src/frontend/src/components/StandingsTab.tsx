import React, { useState, useEffect } from 'react';
import { Trophy } from 'lucide-react';

interface StandingsTabProps {
  serverUrl: string;
  lang: string;
}

interface TeamStanding {
  team: string;
  p: number;
  w: number;
  d: number;
  l: number;
  gf: number;
  ga: number;
  gd: number;
  pts: number;
}

interface Group {
  name: string;
  standings: TeamStanding[];
}

interface BracketMatch {
  id: string;
  team1: string;
  team2: string;
  score1: number | null;
  score2: number | null;
  winner: string | null;
}

interface BracketData {
  groups: Group[];
  r32: BracketMatch[];
  r16: BracketMatch[];
  qf: BracketMatch[];
  sf: BracketMatch[];
  final: BracketMatch[];
  third: BracketMatch[];
}

export const StandingsTab: React.FC<StandingsTabProps> = ({ serverUrl, lang }) => {
  const [data, setData] = useState<BracketData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<'groups' | 'bracket'>('groups');
  const [bracketRound, setBracketRound] = useState<'all' | 'r32' | 'r16' | 'qf' | 'sf' | 'final'>('all');

  useEffect(() => {
    const fetchStandings = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${serverUrl}/api/standings`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (err) {
        console.error('Error fetching standings and bracket state', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStandings();
  }, [serverUrl]);

  if (loading || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] gap-3">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium text-slate-400">
          {lang === 'Español' ? 'Cargando clasificaciones y llaves...' : 'Fetching standings and bracket...'}
        </span>
      </div>
    );
  }

  const translateText = (text: string) => {
    if (lang === 'English') return text;
    const map: Record<string, string> = {
      'Tournament Standings': 'Tabla del Torneo',
      'Group Stage': 'Fase de Grupos',
      'Knockout Bracket': 'Llaves de Eliminación',
      'Team': 'Equipo',
      'P': 'PJ',
      'W': 'PG',
      'D': 'PE',
      'L': 'PP',
      'GD': 'DG',
      'Pts': 'Pts',
      'Round of 32': 'Ronda de 32 (Dieciseisavos)',
      'Round of 16': 'Octavos de Final',
      'Quarterfinals': 'Cuartos de Final',
      'Semifinals': 'Semifinales',
      'Final': 'Final',
      'Third Place': 'Tercer Lugar',
      'Third Place Playoff': 'Partido por el Tercer Puesto',
      'All Rounds': 'Todas las Rondas',
    };
    
    if (text.startsWith('Group ')) {
      return text.replace('Group ', 'Grupo ');
    }
    return map[text] || text;
  };

  const renderMatchCard = (match: BracketMatch) => {
    const t1Winner = match.winner === match.team1 && match.team1 !== '???';
    const t2Winner = match.winner === match.team2 && match.team2 !== '???';

    return (
      <div
        key={match.id}
        className="bg-slate-900/60 border border-slate-800/40 rounded-xl p-3.5 flex flex-col justify-center gap-2 hover:border-emerald-500/30 transition-all duration-200"
      >
        <div className="flex justify-between items-center text-xs">
          <span className={`font-semibold flex items-center gap-1.5 ${t1Winner ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
            {match.team1}
          </span>
          <span className="font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800/60 text-slate-200">
            {match.score1 !== null ? match.score1 : '-'}
          </span>
        </div>
        <div className="flex justify-between items-center text-xs">
          <span className={`font-semibold flex items-center gap-1.5 ${t2Winner ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
            {match.team2}
          </span>
          <span className="font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800/60 text-slate-200">
            {match.score2 !== null ? match.score2 : '-'}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Tab controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/40 p-4 rounded-xl border border-slate-800/40">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-emerald-400" />
            <span>{translateText('Tournament Standings')}</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            FIFA World Cup 2026 Live Tournament Center
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800/60">
          <button
            onClick={() => setViewMode('groups')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-150 ${
              viewMode === 'groups'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {translateText('Group Stage')}
          </button>
          <button
            onClick={() => setViewMode('bracket')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-150 ${
              viewMode === 'bracket'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {translateText('Knockout Bracket')}
          </button>
        </div>
      </div>

      {viewMode === 'groups' ? (
        /* Group Stage Grid Layout */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {data.groups.map((group, groupIdx) => (
            <div key={groupIdx} className="glass-panel p-4 flex flex-col justify-between">
              <h3 className="text-sm font-bold text-slate-200 border-b border-slate-800/60 pb-2 mb-3">
                {translateText(group.name)}
              </h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="text-slate-500 font-mono border-b border-slate-800/40">
                      <th className="py-1 font-medium">{translateText('Team')}</th>
                      <th className="py-1 px-1.5 text-center font-medium">{translateText('P')}</th>
                      <th className="py-1 px-1 text-center font-medium">{translateText('W')}</th>
                      <th className="py-1 px-1 text-center font-medium">{translateText('D')}</th>
                      <th className="py-1 px-1 text-center font-medium">{translateText('L')}</th>
                      <th className="py-1 px-1 text-center font-medium">{translateText('GD')}</th>
                      <th className="py-1 px-1.5 text-right font-medium">{translateText('Pts')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.standings.map((row, rowIdx) => {
                      const isTop2 = rowIdx < 2;
                      const isThird = rowIdx === 2;
                      return (
                        <tr 
                          key={rowIdx} 
                          className={`border-b border-slate-800/30 last:border-0 hover:bg-slate-900/20 transition-all ${
                            isTop2 ? 'text-slate-100' : isThird ? 'text-slate-300' : 'text-slate-500'
                          }`}
                        >
                          <td className="py-2.5 font-semibold flex items-center gap-1.5 truncate max-w-[120px]">
                            <span className={`w-1.5 h-1.5 rounded-full ${
                              isTop2 ? 'bg-emerald-500' : isThird ? 'bg-amber-500' : 'bg-slate-700'
                            }`} />
                            {row.team}
                          </td>
                          <td className="py-2.5 px-1.5 text-center font-mono text-slate-400">{row.p}</td>
                          <td className="py-2.5 px-1 text-center font-mono text-slate-400">{row.w}</td>
                          <td className="py-2.5 px-1 text-center font-mono text-slate-400">{row.d}</td>
                          <td className="py-2.5 px-1 text-center font-mono text-slate-400">{row.l}</td>
                          <td className={`py-2.5 px-1 text-center font-mono ${row.gd > 0 ? 'text-emerald-500' : row.gd < 0 ? 'text-rose-500' : 'text-slate-500'}`}>
                            {row.gd > 0 ? `+${row.gd}` : row.gd}
                          </td>
                          <td className="py-2.5 px-1.5 text-right font-bold font-mono text-emerald-400">{row.pts}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Knockout Stage Bracket View */
        <div className="space-y-4">
          {/* Sub-navigation for Knockout rounds on mobile/tablet */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800/60 max-w-max">
            {[
              { id: 'all', label: translateText('All Rounds') },
              { id: 'r32', label: 'R32' },
              { id: 'r16', label: 'R16' },
              { id: 'qf', label: 'QF' },
              { id: 'sf', label: 'SF' },
              { id: 'final', label: 'Finals' },
            ].map((round) => (
              <button
                key={round.id}
                onClick={() => setBracketRound(round.id as any)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-150 ${
                  bracketRound === round.id
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {round.label}
              </button>
            ))}
          </div>

          {/* Grid Layout of Bracket */}
          <div className="flex flex-col lg:flex-row gap-6 overflow-x-auto pb-4 min-w-full">
            {/* Round of 32 */}
            {(bracketRound === 'all' || bracketRound === 'r32') && (
              <div className="flex-1 min-w-[240px] space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono border-b border-slate-800/60 pb-2">
                  {translateText('Round of 32')}
                </h3>
                <div className="flex flex-col gap-4">
                  {data.r32.map(renderMatchCard)}
                </div>
              </div>
            )}

            {/* Round of 16 */}
            {(bracketRound === 'all' || bracketRound === 'r16') && (
              <div className="flex-1 min-w-[240px] space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono border-b border-slate-800/60 pb-2">
                  {translateText('Round of 16')}
                </h3>
                <div className="flex flex-col gap-8 justify-around h-full py-4">
                  {data.r16.map(renderMatchCard)}
                </div>
              </div>
            )}

            {/* Quarterfinals */}
            {(bracketRound === 'all' || bracketRound === 'qf') && (
              <div className="flex-1 min-w-[240px] space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono border-b border-slate-800/60 pb-2">
                  {translateText('Quarterfinals')}
                </h3>
                <div className="flex flex-col gap-16 justify-around h-full py-12">
                  {data.qf.map(renderMatchCard)}
                </div>
              </div>
            )}

            {/* Semifinals */}
            {(bracketRound === 'all' || bracketRound === 'sf') && (
              <div className="flex-1 min-w-[240px] space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono border-b border-slate-800/60 pb-2">
                  {translateText('Semifinals')}
                </h3>
                <div className="flex flex-col gap-32 justify-around h-full py-24">
                  {data.sf.map(renderMatchCard)}
                </div>
              </div>
            )}

            {/* Finals (Final & Third Place Playoff) */}
            {(bracketRound === 'all' || bracketRound === 'final') && (
              <div className="flex-1 min-w-[240px] space-y-6">
                <div>
                  <h3 className="text-xs font-bold text-rose-400 uppercase tracking-widest font-mono border-b border-rose-500/20 pb-2 mb-4">
                    {translateText('Final')}
                  </h3>
                  <div className="flex flex-col gap-4">
                    {data.final.map(renderMatchCard)}
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono border-b border-slate-800/60 pb-2 mb-4">
                    {translateText('Third Place Playoff')}
                  </h3>
                  <div className="flex flex-col gap-4">
                    {data.third.map(renderMatchCard)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
