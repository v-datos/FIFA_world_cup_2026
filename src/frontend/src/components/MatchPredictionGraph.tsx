import React from 'react';
import { ShieldCheck, BarChart3, HelpCircle } from 'lucide-react';

interface MatchPredictionGraphProps {
  team1: string;
  team2: string;
  probabilities: {
    team1_win: number;
    draw: number;
    team2_win: number;
    confidence?: number;
  };
  scoreProbs?: Array<{ score: string; probability: number }>;
  lang: string;
}

export const MatchPredictionGraph: React.FC<MatchPredictionGraphProps> = ({
  team1,
  team2,
  probabilities,
  scoreProbs = [],
  lang,
}) => {
  const t1Win = probabilities.team1_win || 0.40;
  const t2Win = probabilities.team2_win || 0.30;
  const confidence = probabilities.confidence !== undefined ? probabilities.confidence : 0.78;

  const t1Pct = Math.round(t1Win * 100);
  const t2Pct = Math.round(t2Win * 100);
  const drawPct = 100 - (t1Pct + t2Pct);

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

  return (
    <div className="w-full glass-panel p-5 flex flex-col justify-between space-y-6">
      <div>
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-3">
          <BarChart3 className="w-5 h-5 text-emerald-400" />
          <span>{translateText('Match Outcome Probability')}</span>
        </h3>

        {/* Stacked Outcome Bar */}
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
              {team1.toUpperCase()} {translateText('WIN')}
            </span>
            <span className="text-slate-400">
              {translateText('DRAW')}
            </span>
            <span className="text-rose-400 flex items-center gap-1">
              {team2.toUpperCase()} {translateText('WIN')}
            </span>
          </div>
        </div>

        {/* Top Exact Scores (integrated) */}
        {scoreProbs.length > 0 && (
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

      {/* Model Information Container */}
      <div className="pt-4 border-t border-slate-800/60 space-y-4">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>{translateText('Model Methodology & Info')}</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/40 flex flex-col justify-between">
            <span className="text-slate-500 font-medium">{translateText('Model Used')}</span>
            <span className="font-bold text-slate-200 mt-1 font-mono text-[11px]">{translateText('Dixon-Coles Poisson Solver')}</span>
            <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">
              {translateText('Bivariate Poisson solver utilizing Elo ratings with low-score correlation adjustment.')}
            </p>
          </div>

          <div className="bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/40 flex flex-col justify-between">
            <span className="text-slate-500 font-medium">{translateText('Input Sources')}</span>
            <span className="font-bold text-slate-200 mt-1 font-mono text-[11px]">Dynamic Club ELO</span>
            <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">
              {translateText('Dynamic Club Elo ratings from SoccerData scraped endpoints.')}
            </p>
          </div>
        </div>

        <div className="flex justify-between items-center text-xs pt-1">
          <span className="text-slate-400 flex items-center gap-1 font-medium">
            <HelpCircle className="w-4 h-4 text-slate-500" />
            {translateText('Confidence Rating')}
          </span>
          <span className="text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-mono font-bold">
            {Math.round(confidence * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
};
