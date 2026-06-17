import React from 'react';
import { Dices } from 'lucide-react';
import { getFlag } from '../lib/teamData';

interface Props {
  team1: string;
  team2: string;
  proj1?: Record<string, any>;
  proj2?: Record<string, any>;
  lang: string;
}

export const MonteCarloProjections: React.FC<Props> = ({
  team1,
  team2,
  proj1 = {},
  proj2 = {},
  lang,
}) => {
  const es = lang === 'Español';

  const stages: { key: string; label: string }[] = [
    { key: 'r16', label: es ? 'Alcanzar Octavos' : 'Reach Round of 16' },
    { key: 'qf', label: es ? 'Alcanzar Cuartos' : 'Reach Quarterfinals' },
    { key: 'sf', label: es ? 'Alcanzar Semifinales' : 'Reach Semifinals' },
    { key: 'final', label: es ? 'Alcanzar la Final' : 'Reach Final' },
    { key: 'win', label: es ? 'Ganar el Mundial' : 'Win World Cup' },
  ];

  const pct = (v: any): string => (typeof v === 'number' ? `${Math.round(v * 100)}%` : 'N/A');
  const width = (v: any): number => (typeof v === 'number' ? Math.max(2, Math.round(v * 100)) : 0);

  return (
    <div className="w-full glass-panel p-5">
      <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-1">
        <Dices className="w-5 h-5 text-emerald-400" />
        <span>{es ? 'Proyecciones de Simulación Monte Carlo' : 'Monte Carlo Simulation Projections'}</span>
      </h3>
      <div className="flex justify-between items-center text-sm font-bold mt-3 mb-3">
        <span className="text-emerald-400">{getFlag(team1)} {team1}</span>
        <span className="text-rose-400">{team2} {getFlag(team2)}</span>
      </div>

      <div className="space-y-3.5">
        {stages.map((s) => {
          const p1 = proj1[s.key];
          const p2 = proj2[s.key];
          return (
            <div key={s.key}>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="text-emerald-400 font-mono font-bold w-12 text-left">{pct(p1)}</span>
                <span className="text-slate-400 text-[11px] font-medium text-center flex-1">{s.label}</span>
                <span className="text-rose-400 font-mono font-bold w-12 text-right">{pct(p2)}</span>
              </div>
              <div className="flex gap-1 h-2">
                <div className="flex-1 bg-slate-800/60 rounded-full overflow-hidden flex justify-end">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${width(p1)}%` }} />
                </div>
                <div className="flex-1 bg-slate-800/60 rounded-full overflow-hidden">
                  <div className="bg-rose-500 h-full rounded-full" style={{ width: `${width(p2)}%` }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
