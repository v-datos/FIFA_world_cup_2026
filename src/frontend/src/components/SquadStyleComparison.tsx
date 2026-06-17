import React from 'react';
import { getFlag } from '../lib/teamData';

interface Props {
  team1: string;
  team2: string;
  metrics1?: Record<string, any>;
  metrics2?: Record<string, any>;
  elo1?: number | null;
  elo2?: number | null;
  lang: string;
}

type Row = {
  label: string;
  key?: string;
  elo?: boolean;
  prefix?: string;
  suffix?: string;
  dec: number;
  lowerIsBetter?: boolean;
  neutral?: boolean;
};

export const SquadStyleComparison: React.FC<Props> = ({
  team1,
  team2,
  metrics1 = {},
  metrics2 = {},
  elo1,
  elo2,
  lang,
}) => {
  const es = lang === 'Español';

  const rows: Row[] = [
    { label: es ? 'Posesión Media' : 'Average Possession', key: 'possession_avg', suffix: '%', dec: 1 },
    { label: es ? 'Valor de Plantilla' : 'Squad Market Value', key: 'squad_market_value_m', prefix: '€', suffix: 'M', dec: 1 },
    { label: es ? 'Edad Media' : 'Average Age', key: 'average_age', suffix: ' yrs', dec: 1, neutral: true },
    { label: es ? 'Clasificación Club Elo' : 'Club Elo Rating', elo: true, dec: 0 },
    { label: es ? 'Goles / 90' : 'Goals / 90', key: 'goals_per_90', dec: 2 },
    { label: es ? 'Goles Concedidos / 90' : 'Goals Conceded / 90', key: 'goals_conceded_per_90', dec: 2, lowerIsBetter: true },
    { label: es ? 'Goles Esperados (xG) / 90' : 'Expected Goals (xG) / 90', key: 'expected_goals_per_90', dec: 2 },
    { label: es ? 'xG Concedidos (xGC) / 90' : 'xG Conceded (xGC) / 90', key: 'expected_goals_conceded_per_90', dec: 2, lowerIsBetter: true },
    { label: es ? 'Tiros / 90' : 'Shots / 90', key: 'shots_per_90', dec: 1 },
    { label: es ? 'Tiros a Puerta %' : 'Shots on Target %', key: 'shots_on_target_pct', suffix: '%', dec: 1 },
    { label: es ? 'xG / Tiro' : 'xG / Shot', key: 'xg_per_shot', dec: 3 },
    { label: es ? 'Tiros en Contra / 90' : 'Shots Against / 90', key: 'shots_against_per_90', dec: 1, lowerIsBetter: true },
    { label: es ? 'Pases / 90' : 'Passes / 90', key: 'passes_per_90', dec: 0 },
    { label: es ? 'Precisión de Pase %' : 'Pass Completion %', key: 'pass_completion_pct', suffix: '%', dec: 1 },
    { label: es ? 'PPDA (Intensidad de Presión)' : 'PPDA (Pressing Intensity)', key: 'ppda', dec: 1, lowerIsBetter: true },
    { label: es ? 'Inclinación de Campo %' : 'Field Tilt %', key: 'field_tilt_pct', suffix: '%', dec: 1 },
  ];

  const num = (row: Row, m: Record<string, any>, elo?: number | null): number | null => {
    if (row.elo) return elo ?? null;
    const v = parseFloat(m[row.key as string]);
    return isNaN(v) ? null : v;
  };

  const fmt = (row: Row, v: number | null): string => {
    if (v === null) return '—';
    return `${row.prefix ?? ''}${v.toFixed(row.dec)}${row.suffix ?? ''}`;
  };

  return (
    <div className="w-full h-full glass-panel p-5 flex flex-col">
      <h3 className="text-lg font-bold text-slate-100">
        {es ? 'Comparación de Plantilla y Estilo' : 'Squad & Style Comparison'}
      </h3>
      <p className="text-xs text-slate-400 mb-4">(FBref &amp; Club Elo)</p>

      <div className="flex justify-between items-center text-sm font-bold mb-2 pb-2 border-b border-slate-800/60">
        <span className="text-emerald-400">{getFlag(team1)} {team1}</span>
        <span className="text-rose-400">{team2} {getFlag(team2)}</span>
      </div>

      <div className="flex-1 flex flex-col justify-between mt-1">
        {rows.map((row) => {
          const n1 = num(row, metrics1, elo1);
          const n2 = num(row, metrics2, elo2);
          let better: 1 | 2 | 0 = 0;
          if (!row.neutral && n1 !== null && n2 !== null && n1 !== n2) {
            const oneBetter = row.lowerIsBetter ? n1 < n2 : n1 > n2;
            better = oneBetter ? 1 : 2;
          }
          return (
            <div
              key={row.label}
              className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 py-1 border-b border-slate-800/30 last:border-0"
            >
              <span className={`font-mono text-sm font-bold text-left ${better === 1 ? 'text-emerald-400' : 'text-slate-300'}`}>
                {fmt(row, n1)}
              </span>
              <span className="text-[10px] text-slate-500 text-center uppercase tracking-wide px-1">
                {row.label}
              </span>
              <span className={`font-mono text-sm font-bold text-right ${better === 2 ? 'text-rose-400' : 'text-slate-300'}`}>
                {fmt(row, n2)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
