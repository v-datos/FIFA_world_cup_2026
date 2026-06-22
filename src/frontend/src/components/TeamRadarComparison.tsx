import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

type MetricValue = number | string | null | undefined;
type MetricRecord = Record<string, MetricValue>;

interface TeamRadarComparisonProps {
  team1: string;
  team2: string;
  metrics1?: MetricRecord;
  metrics2?: MetricRecord;
  quality?: {
    status?: string;
    source_label?: string;
    message?: string;
    missing_fields?: Record<string, string[]>;
  };
  lang: string;
  className?: string;
}

export const TeamRadarComparison: React.FC<TeamRadarComparisonProps> = ({
  team1,
  team2,
  metrics1 = {},
  metrics2 = {},
  quality,
  lang,
  className = "",
}) => {
  // Radar uses the metrics the deterministic ESPN match-stats collector provides
  // for every played match. xG/PPDA are not exposed by that feed, so they are
  // not required here (see collect_espn_matchday.py / DEC024).
  const requiredFields = [
    'possession_avg',
    'shots_per_90',
    'shots_on_target_pct',
    'pass_completion_pct',
  ];

  const toNumber = (value: MetricValue): number => {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') return Number.parseFloat(value);
    return Number.NaN;
  };

  const missingFields = (metrics: MetricRecord) => (
    requiredFields.filter((field) => {
      const value = toNumber(metrics[field]);
      return metrics[field] === undefined || metrics[field] === null || isNaN(value);
    })
  );

  const t1Missing = missingFields(metrics1);
  const t2Missing = missingFields(metrics2);
  const unavailable = quality?.status === 'unavailable' || t1Missing.length > 0 || t2Missing.length > 0;

  // Map raw data/fallbacks to standardized scale [0 - 100] for visual uniformity
  const prepareRadarData = () => {
    // Labels mapping
    const labels: Record<string, string> = {
      shots: lang === 'Español' ? 'Tiros/90' : 'Shots/90',
      passing: lang === 'Español' ? 'Precisión Pases %' : 'Pass Accuracy %',
      possession: lang === 'Español' ? 'Posesión %' : 'Possession %',
      accuracy: lang === 'Español' ? 'Precisión Tiro %' : 'Shot Accuracy %',
    };

    // Map a real-world value into the 0-100 radar range (higher = better/more).
    const scale = (val: MetricValue, min: number, max: number) => {
      const v = toNumber(val);
      return Math.round(Math.max(10, Math.min(100, ((v - min) / (max - min)) * 90 + 10)));
    };

    const t1 = metrics1 || {};
    const t2 = metrics2 || {};

    return [
      {
        subject: labels.possession,
        [team1]: scale(t1.possession_avg, 35.0, 65.0),
        [team2]: scale(t2.possession_avg, 35.0, 65.0),
      },
      {
        subject: labels.shots,
        [team1]: scale(t1.shots_per_90, 5.0, 20.0),
        [team2]: scale(t2.shots_per_90, 5.0, 20.0),
      },
      {
        subject: labels.accuracy,
        [team1]: scale(t1.shots_on_target_pct, 20.0, 60.0),
        [team2]: scale(t2.shots_on_target_pct, 20.0, 60.0),
      },
      {
        subject: labels.passing,
        [team1]: scale(t1.pass_completion_pct, 60.0, 92.0),
        [team2]: scale(t2.pass_completion_pct, 60.0, 92.0),
      },
    ];
  };

  const data = unavailable ? [] : prepareRadarData();
  const sourceLabel = quality?.source_label?.replace(/_/g, ' ') || 'static curated';

  return (
    <div className={`w-full glass-panel p-5 flex flex-col justify-between ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-bold text-slate-100">
            {lang === 'Español' ? 'Comparación de Rendimiento' : 'Team Performance Metrics'}
          </h3>
          <p className="text-xs text-slate-400">
            {unavailable
              ? (lang === 'Español' ? 'Métricas insuficientes para graficar' : 'Insufficient metrics to chart')
              : (lang === 'Español' ? 'Comparación estadística normalizada' : 'Normalized tactical style comparison')}
          </p>
        </div>
        
        {/* Legend */}
        <div className="flex gap-4 text-xs font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-500" />
            <span className="text-slate-300">{team1}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-rose-500" />
            <span className="text-slate-300">{team2}</span>
          </div>
        </div>
      </div>

      <div className="w-full h-[280px] flex items-center justify-center">
        {unavailable ? (
          <div className="w-full rounded-xl border border-amber-500/25 bg-amber-500/10 p-4 text-center">
            <div className="text-sm font-bold text-amber-300">
              {lang === 'Español' ? 'Radar no disponible' : 'Radar unavailable'}
            </div>
            <p className="text-xs text-amber-100/75 mt-2 leading-relaxed">
              {quality?.message || (lang === 'Español'
                ? 'Faltan métricas requeridas para uno o ambos equipos.'
                : 'Required metrics are missing for one or both teams.')}
            </p>
            <div className="mt-3 text-[10px] uppercase tracking-wide text-amber-200/70 font-mono">
              {sourceLabel}
            </div>
          </div>
        ) : (
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
            <PolarGrid stroke="rgba(71, 85, 105, 0.4)" />
            <PolarAngleAxis 
              dataKey="subject" 
              tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'Outfit, sans-serif' }}
            />
            <PolarRadiusAxis 
              angle={30} 
              domain={[0, 100]} 
              tick={false} 
              axisLine={false} 
            />
            <Radar
              name={team1}
              dataKey={team1}
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.25}
            />
            <Radar
              name={team2}
              dataKey={team2}
              stroke="#f43f5e"
              fill="#f43f5e"
              fillOpacity={0.25}
            />
          </RadarChart>
        </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
