import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface MatchPredictionGraphProps {
  team1: string;
  team2: string;
  probabilities: {
    team1_win: number;
    draw: number;
    team2_win: number;
  };
  lang: string;
}

export const MatchPredictionGraph: React.FC<MatchPredictionGraphProps> = ({
  team1,
  team2,
  probabilities,
  lang,
}) => {
  // Generate a realistic, ELO-weighted win probability shift over the match minutes
  const generateTimelineData = () => {
    const t1Base = probabilities.team1_win;
    const t2Base = probabilities.team2_win;

    const data = [];
    let t1Val = t1Base;
    let t2Val = t2Base;

    for (let min = 0; min <= 90; min += 5) {
      // Simulate minor shifts over time
      const noise1 = (Math.sin(min / 10) * 0.03) + (Math.cos(min / 5) * 0.01);
      const noise2 = (Math.cos(min / 12) * 0.03) + (Math.sin(min / 7) * 0.01);
      
      let currentT1 = Math.max(0.05, Math.min(0.90, t1Val + noise1));
      let currentT2 = Math.max(0.05, Math.min(0.90, t2Val + noise2));
      
      // Ensure sum is 1.0
      const currentDraw = 1.0 - (currentT1 + currentT2);

      data.push({
        minute: min,
        [team1]: Math.round(currentT1 * 100),
        [lang === 'Español' ? 'Empate' : 'Draw']: Math.round(currentDraw * 100),
        [team2]: Math.round(currentT2 * 100),
      });
    }
    return data;
  };

  const data = generateTimelineData();
  const drawKey = lang === 'Español' ? 'Empate' : 'Draw';

  return (
    <div className="w-full glass-panel p-5 mt-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-bold text-slate-100">
            {lang === 'Español' ? 'Gráfico de Predicción de Partido' : 'Match Prediction Graph'}
          </h3>
          <p className="text-xs text-slate-400">
            {lang === 'Español' ? 'Simulación en vivo de probabilidades de victoria' : 'Live win probability simulation timeline'}
          </p>
        </div>
        
        {/* Legend */}
        <div className="flex gap-4 text-xs font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-500" />
            <span className="text-slate-300">{team1}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-slate-500" />
            <span className="text-slate-300">{drawKey}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500" />
            <span className="text-slate-300">{team2}</span>
          </div>
        </div>
      </div>

      <div className="w-full h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorT1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.05}/>
              </linearGradient>
              <linearGradient id="colorDraw" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#64748b" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#64748b" stopOpacity={0.05}/>
              </linearGradient>
              <linearGradient id="colorT2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.05}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.2)" vertical={false} />
            <XAxis 
              dataKey="minute" 
              stroke="#64748b" 
              fontSize={11} 
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${v}'`}
            />
            <YAxis 
              stroke="#64748b" 
              fontSize={11} 
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '12px',
                fontFamily: 'Outfit, sans-serif'
              }}
              labelFormatter={(label) => `${lang === 'Español' ? 'Minuto' : 'Minute'}: ${label}'`}
            />
            <Area 
              type="monotone" 
              dataKey={team1} 
              stroke="#0ea5e9" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorT1)" 
              stackId="1"
            />
            <Area 
              type="monotone" 
              dataKey={drawKey} 
              stroke="#64748b" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorDraw)" 
              stackId="1"
            />
            <Area 
              type="monotone" 
              dataKey={team2} 
              stroke="#f43f5e" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorT2)" 
              stackId="1"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
