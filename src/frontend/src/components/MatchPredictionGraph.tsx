import React from 'react';
import { BarChart3, HelpCircle } from 'lucide-react';
import { translateTeamName } from '../lib/translations';

interface MatchPredictionGraphProps {
  team1: string;
  team2: string;
  probabilities: {
    team1_win?: number | null;
    draw?: number | null;
    team2_win?: number | null;
    confidence?: number | null;
  };
  scoreProbs?: Array<{ score: string; probability: number }>;
  quality?: {
    status?: string;
    source_label?: string;
    message?: string;
  };
  scoreQuality?: {
    status?: string;
    source_label?: string;
    message?: string;
  };
  lang: string;
}

export const MatchPredictionGraph: React.FC<MatchPredictionGraphProps> = ({
  team1,
  team2,
  probabilities,
  scoreProbs = [],
  quality,
  scoreQuality,
  lang,
}) => {
  const forecastUnavailable = (
    quality?.status === 'unavailable' ||
    probabilities.team1_win == null ||
    probabilities.draw == null ||
    probabilities.team2_win == null
  );
  const scoresUnavailable = forecastUnavailable || scoreQuality?.status === 'unavailable';

  const t1Win = probabilities.team1_win ?? 0;
  const t2Win = probabilities.team2_win ?? 0;
  const draw = probabilities.draw ?? 0;
  const confidence = probabilities.confidence ?? null;

  const t1Pct = Math.round(t1Win * 100);
  const t2Pct = Math.round(t2Win * 100);
  const drawPct = Math.round(draw * 100);

  const translateText = (text: string) => {
    if (lang === 'English') return text;
    const map: Record<string, string> = {
      'Match Outcome Probability': 'Probabilidad de Resultado del Partido',
      'Model Methodology & Info': 'Metodología del Modelo e Información',
      'Model Used': 'Modelo Utilizado',
      'Confidence Rating': 'Calificación de Confianza',
      'Input Sources': 'Fuentes de Entrada',
      'Dixon-Coles Poisson Solver': 'Solucionador Poisson Dixon-Coles',
      'Bivariate Poisson solver utilizing Elo ratings with low-score correlation adjustment.': 
        'Solucionador Poisson bivariado que utiliza clasificaciones Elo con ajuste de correlación para marcadores bajos.',
      'Dynamic Club Elo ratings from SoccerData scraped endpoints.': 
        'Clasificaciones dinámicas de Club Elo de los endpoints de SoccerData.',
      'WIN': 'VICTORIA',
      'DRAW': 'EMPATE',
      'Top Exact Scores': 'Marcadores Exactos Principales'
    };
    return map[text] || text;
  };

  const sourceLabel = quality?.source_label?.replace(/_/g, ' ') || 'unknown';

  return (
    <div className="w-full glass-panel p-5 flex flex-col justify-between space-y-6">
      <div>
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-3">
          <BarChart3 className="w-5 h-5 text-emerald-400" />
          <span>{translateText('Match Outcome Probability')}</span>
        </h3>

        {forecastUnavailable ? (
          <div className="rounded-xl border border-amber-500/25 bg-amber-500/10 p-4">
            <div className="flex items-center gap-2 text-amber-300 font-bold text-sm">
              <HelpCircle className="w-4 h-4" />
              <span>{lang === 'Español' ? 'Pronóstico no disponible' : 'Forecast unavailable'}</span>
            </div>
            <p className="text-xs text-amber-100/75 mt-2 leading-relaxed">
              {quality?.message || (lang === 'Español'
                ? 'Este partido solo tiene un valor de respaldo y no se muestra como probabilidad del modelo.'
                : 'This fixture only has a fallback value and is not shown as a model probability.')}
            </p>
            <div className="mt-3 text-[10px] uppercase tracking-wide text-amber-200/70 font-mono">
              {sourceLabel}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="w-full h-11 bg-slate-900/40 rounded-xl overflow-hidden flex border border-slate-800/60 p-1">
              {t1Pct > 0 && (
                <div
                  className="h-full bg-gradient-to-r from-sky-500 to-sky-400 rounded-lg flex items-center justify-center text-xs font-bold text-slate-950 transition-all duration-300"
                  style={{ width: `${t1Pct}%` }}
                >
                  {t1Pct >= 10 && `${t1Pct}%`}
                </div>
              )}
              {drawPct > 0 && (
                <div
                  className="h-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300 transition-all duration-300 mx-1 rounded-md"
                  style={{ width: `${drawPct}%` }}
                >
                  {drawPct >= 10 && `${drawPct}%`}
                </div>
              )}
              {t2Pct > 0 && (
                <div
                  className="h-full bg-gradient-to-r from-rose-500 to-rose-400 rounded-lg flex items-center justify-center text-xs font-bold text-slate-950 transition-all duration-300"
                  style={{ width: `${t2Pct}%` }}
                >
                  {t2Pct >= 10 && `${t2Pct}%`}
                </div>
              )}
            </div>

            {/* Outcome Bar Labels */}
            <div className="flex justify-between text-xs font-semibold px-1">
              <span className="text-sky-400 flex items-center gap-1">
                {lang === 'Español'
                  ? `VICTORIA DE ${translateTeamName(team1, lang).toUpperCase()}`
                  : `${team1.toUpperCase()} WIN`}
              </span>
              <span className="text-slate-400">
                {translateText('DRAW')}
              </span>
              <span className="text-rose-400 flex items-center gap-1">
                {lang === 'Español'
                  ? `VICTORIA DE ${translateTeamName(team2, lang).toUpperCase()}`
                  : `${team2.toUpperCase()} WIN`}
              </span>
            </div>
          </div>
        )}

        {/* Top Exact Scores (integrated) */}
        {!scoresUnavailable && scoreProbs.length > 0 && (
          <div className="mt-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              {translateText('Top Exact Scores')}
            </h4>
            <div className="grid grid-cols-3 gap-2">
              {scoreProbs.slice(0, 6).map((item, idx) => (
                <div key={idx} className="bg-slate-900/60 border border-slate-800/40 rounded-lg px-2 py-1.5 flex justify-between items-center">
                  <span className="font-bold text-xs text-slate-200 font-mono">{item.score}</span>
                  <span className="text-[11px] text-emerald-400 font-mono font-semibold">{Math.round(item.probability * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {!forecastUnavailable && (
        <div className="pt-4 border-t border-slate-800/60 flex justify-between items-center text-xs">
          <span className="text-slate-400 flex items-center gap-1 font-medium">
            <HelpCircle className="w-4 h-4 text-slate-500" />
            {translateText('Confidence Rating')}
          </span>
          <span className="text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-mono font-bold">
            {confidence === null ? 'N/A' : `${Math.round(confidence * 100)}%`}
          </span>
        </div>
      )}
    </div>
  );
};
