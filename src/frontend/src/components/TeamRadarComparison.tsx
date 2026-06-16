import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

interface TeamRadarComparisonProps {
  team1: string;
  team2: string;
  metrics1?: Record<string, any>;
  metrics2?: Record<string, any>;
  lang: string;
}

export const TeamRadarComparison: React.FC<TeamRadarComparisonProps> = ({
  team1,
  team2,
  metrics1 = {},
  metrics2 = {},
  lang,
}) => {
  // Map raw data/fallbacks to standardized scale [0 - 100] for visual uniformity
  const prepareRadarData = () => {
    // Labels mapping
    const labels: Record<string, string> = {
      xg: lang === 'Español' ? 'Goles Esperados (xG)' : 'Expected Goals (xG)',
      shots: lang === 'Español' ? 'Tiros/90' : 'Shots/90',
      passing: lang === 'Español' ? 'Precisión Pases %' : 'Pass Accuracy %',
      tackles: lang === 'Español' ? 'Tackles/90' : 'Tackles/90',
      pressure: lang === 'Español' ? 'Intensidad Presión %' : 'Press Intensity %',
      possession: lang === 'Español' ? 'Posesión %' : 'Possession %',
    };

    // Scaled metrics (mapping real-world values to a 0-100 range)
    const scale = (val: number, min: number, max: number) => {
      if (val === undefined || val === null || isNaN(val)) return 50;
      return Math.round(Math.max(10, Math.min(100, ((val - min) / (max - min)) * 90 + 10)));
    };

    const t1 = metrics1 || {};
    const t2 = metrics2 || {};

    return [
      {
        subject: labels.xg,
        [team1]: scale(parseFloat(t1.xg_90 || t1.avg_xg || 1.2), 0.5, 2.5),
        [team2]: scale(parseFloat(t2.xg_90 || t2.avg_xg || 1.0), 0.5, 2.5),
      },
      {
        subject: labels.shots,
        [team1]: scale(parseFloat(t1.shots_90 || t1.avg_shots || 10.0), 5.0, 20.0),
        [team2]: scale(parseFloat(t2.shots_90 || t2.avg_shots || 8.0), 5.0, 20.0),
      },
      {
        subject: labels.passing,
        [team1]: scale(parseFloat(t1.pass_completion || t1.pass_accuracy || 80.0), 60.0, 95.0),
        [team2]: scale(parseFloat(t2.pass_completion || t2.pass_accuracy || 78.0), 60.0, 95.0),
      },
      {
        subject: labels.tackles,
        [team1]: scale(parseFloat(t1.tackles_90 || t1.avg_tackles || 14.0), 5.0, 25.0),
        [team2]: scale(parseFloat(t2.tackles_90 || t2.avg_tackles || 16.0), 5.0, 25.0),
      },
      {
        subject: labels.pressure,
        [team1]: scale(parseFloat(t1.pressure_regain_pct || 22.0), 10.0, 45.0),
        [team2]: scale(parseFloat(t2.pressure_regain_pct || 25.0), 10.0, 45.0),
      },
      {
        subject: labels.possession,
        [team1]: scale(parseFloat(t1.possession || t1.average_possession || 50.0), 35.0, 65.0),
        [team2]: scale(parseFloat(t2.possession || t2.average_possession || 48.0), 35.0, 65.0),
      },
    ];
  };

  const data = prepareRadarData();

  return (
    <div className="w-full glass-panel p-5">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-bold text-slate-100">
            {lang === 'Español' ? 'Comparación de Rendimiento' : 'Team Performance Metrics'}
          </h3>
          <p className="text-xs text-slate-400">
            {lang === 'Español' ? 'Comparación estadística normalizada' : 'Normalized tactical style comparison'}
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
      </div>
    </div>
  );
};
