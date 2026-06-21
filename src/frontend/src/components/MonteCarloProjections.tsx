import React from 'react';
import { Dices } from 'lucide-react';
import { getFlag } from '../lib/teamData';
import { translateTeamName, translateSimMessage, translateSourceLabel } from '../lib/translations';

type ProjectionValue = number | string | null | undefined;

interface Props {
  team1: string;
  team2: string;
  proj1?: Record<string, ProjectionValue>;
  proj2?: Record<string, ProjectionValue>;
  quality?: {
    status?: string;
    source_label?: string;
    message?: string;
    simulation_count?: number;
    seed?: number;
    model_version?: string;
    rating_status?: string;
  };
  lang: string;
  noWrapper?: boolean;
}

export const MonteCarloProjections: React.FC<Props> = ({
  team1,
  team2,
  proj1 = {},
  proj2 = {},
  quality,
  lang,
  noWrapper = false,
}) => {
  const es = lang === 'Español';
  const deterministicFallback = quality?.status === 'deterministic_fallback';
  const simulation = quality?.status === 'simulation';
  const rawSourceLabel = quality?.source_label || 'hardcoded_reference';
  const sourceLabel = translateSourceLabel(rawSourceLabel, lang) || rawSourceLabel.replace(/_/g, ' ');
  const simulationDetails = [
    quality?.simulation_count ? `${quality.simulation_count.toLocaleString()} ${es ? 'ensayos' : 'trials'}` : null,
    quality?.seed !== undefined ? `seed ${quality.seed}` : null,
    quality?.model_version,
    quality?.rating_status ? (es ? (quality.rating_status === 'complete' ? 'completo' : quality.rating_status === 'partial' ? 'parcial' : 'no disponible') : quality.rating_status.replace(/_/g, ' ')) : null,
  ].filter(Boolean).join(' · ');

  const stages: { key: string; label: string }[] = [
    { key: 'r16', label: es ? 'Alcanzar Octavos' : 'Reach Round of 16' },
    { key: 'qf', label: es ? 'Alcanzar Cuartos' : 'Reach Quarterfinals' },
    { key: 'sf', label: es ? 'Alcanzar Semifinales' : 'Reach Semifinals' },
    { key: 'final', label: es ? 'Alcanzar la Final' : 'Reach Final' },
    { key: 'win', label: es ? 'Ganar el Mundial' : 'Win World Cup' },
  ];

  const pct = (v: ProjectionValue): string => (typeof v === 'number' ? `${Math.round(v * 100)}%` : 'N/A');
  const width = (v: ProjectionValue): number => (typeof v === 'number' ? Math.max(2, Math.round(v * 100)) : 0);

  const renderContent = () => (
    <>
      <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-1">
        <Dices className="w-5 h-5 text-emerald-400" />
        <span>
          {deterministicFallback
            ? (es ? 'Estimación de Progresión del Torneo' : 'Tournament Progression Estimate')
            : (es ? 'Proyecciones de Simulación Monte Carlo' : 'Monte Carlo Simulation Projections')}
        </span>
      </h3>
      {deterministicFallback && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100/75 leading-relaxed">
          {quality?.message || (es
            ? 'Estimación determinística; no es una simulación Monte Carlo con ensayos aleatorios.'
            : 'Deterministic estimate; not a random-trial Monte Carlo simulation.')}
          <span className="block mt-1 uppercase tracking-wide text-amber-200/70 font-mono">{sourceLabel}</span>
        </div>
      )}
      {simulation && (
        <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/5 px-3 py-2 text-[11px] text-slate-300/80 leading-relaxed">
          {translateSimMessage(quality?.message, lang) || (es
            ? 'Simulación con ensayos aleatorios basada en referencias Elo locales.'
            : 'Random-trial simulation based on local Elo-style reference ratings.')}
          <span className="block mt-1 uppercase tracking-wide text-emerald-200/70 font-mono">
            {sourceLabel}{simulationDetails ? ` · ${simulationDetails}` : ''}
          </span>
        </div>
      )}
      <div className="flex justify-between items-center text-sm font-bold mt-3 mb-3">
        <span className="text-emerald-400">{getFlag(team1)} {translateTeamName(team1, lang)}</span>
        <span className="text-rose-400">{translateTeamName(team2, lang)} {getFlag(team2)}</span>
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
    </>
  );

  if (noWrapper) {
    return <div className="space-y-4">{renderContent()}</div>;
  }

  return (
    <div className="w-full glass-panel p-5">
      {renderContent()}
    </div>
  );
};
