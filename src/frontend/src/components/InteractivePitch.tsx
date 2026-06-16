import React, { useState } from 'react';

interface Player {
  name: string;
  position: string;
  club?: string;
  resolvedIds?: {
    statsbomb?: string;
    transfermarkt?: string;
    fbref?: string;
  };
}

interface InteractivePitchProps {
  teamName: string;
  players: string[];
  formation: string;
  playerClubs?: Record<string, string>;
  lang: string;
}

export const InteractivePitch: React.FC<InteractivePitchProps> = ({
  teamName,
  players,
  formation,
  playerClubs = {},
  lang,
}) => {
  const [hoveredPlayer, setHoveredPlayer] = useState<string | null>(null);

  // Parse formation (e.g., "4-3-3", "4-2-3-1", "3-5-2") and map to coordinates
  // Returns percentages for bottom/left positions
  const getCoordinates = (index: number, total: number, lineIndex: number, totalLines: number) => {
    // lineIndex: 0 = GK, 1 = DF, 2 = MF, 3 = FW
    const y = 10 + (lineIndex / (totalLines - 1)) * 80; // y-coordinate from 10% to 90%
    const x = 10 + ((index + 1) / (total + 1)) * 80; // x-coordinate distributed evenly
    return { x, y };
  };

  // Group players by position categories
  const categorizePlayers = () => {
    const gk: Player[] = [];
    const df: Player[] = [];
    const mf: Player[] = [];
    const fw: Player[] = [];

    // Formations categorization rules
    const defCount = parseInt(formation.split('-')[0]) || 4;
    const midCount = parseInt(formation.split('-')[1]) || 3;

    players.forEach((pName, idx) => {
      const pData: Player = {
        name: pName,
        position: 'Player',
        club: playerClubs[pName] || 'Free Agent',
        resolvedIds: {
          statsbomb: `SB-${pName.substring(0, 3).toUpperCase()}-${Math.floor(1000 + Math.random() * 9000)}`,
          transfermarkt: `TM-${pName.replace(' ', '-').toLowerCase()}`,
          fbref: `FB-${pName.substring(0, 4).toUpperCase()}`
        }
      };

      if (idx === 0) {
        pData.position = lang === 'Español' ? 'Portero' : 'Goalkeeper';
        gk.push(pData);
      } else if (idx <= defCount) {
        pData.position = lang === 'Español' ? 'Defensor' : 'Defender';
        df.push(pData);
      } else if (idx <= defCount + midCount) {
        pData.position = lang === 'Español' ? 'Centrocampista' : 'Midfielder';
        mf.push(pData);
      } else {
        pData.position = lang === 'Español' ? 'Delantero' : 'Forward';
        fw.push(pData);
      }
    });

    return [gk, df, mf, fw].filter(arr => arr.length > 0);
  };

  const lines = categorizePlayers();
  const totalLines = lines.length;

  return (
    <div className="w-full flex flex-col items-center">
      <div className="text-center mb-4">
        <h4 className="text-lg font-semibold text-slate-100">{teamName}</h4>
        <span className="text-sm text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 font-mono">
          {formation}
        </span>
      </div>

      {/* Styled Tactical Football Pitch */}
      <div className="relative w-full max-w-[420px] aspect-[3/4] bg-emerald-950/20 border-2 border-emerald-500/30 rounded-xl overflow-hidden shadow-2xl backdrop-blur-md">
        
        {/* Pitch markings */}
        <div className="absolute inset-x-0 top-0 h-1/2 border-b border-emerald-500/20" />
        {/* Center circle */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 border border-emerald-500/20 rounded-full" />
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-emerald-500/30 rounded-full" />
        
        {/* Penalty areas */}
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-48 h-20 border-x border-b border-emerald-500/20" />
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-24 h-8 border-x border-b border-emerald-500/20" />
        
        <div className="absolute left-1/2 bottom-0 -translate-x-1/2 w-48 h-20 border-x border-t border-emerald-500/20" />
        <div className="absolute left-1/2 bottom-0 -translate-x-1/2 w-24 h-8 border-x border-t border-emerald-500/20" />

        {/* Players mapping */}
        {lines.map((linePlayers, lineIdx) => (
          <React.Fragment key={lineIdx}>
            {linePlayers.map((player, pIdx) => {
              const { x, y } = getCoordinates(pIdx, linePlayers.length, lineIdx, totalLines);
              const isHovered = hoveredPlayer === player.name;

              return (
                <div
                  key={player.name}
                  className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer z-10"
                  style={{ left: `${x}%`, bottom: `${y}%` }}
                  onMouseEnter={() => setHoveredPlayer(player.name)}
                  onMouseLeave={() => setHoveredPlayer(null)}
                >
                  {/* Player Dot */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shadow-lg transition-all duration-200 border-2 ${
                    isHovered 
                      ? 'bg-emerald-400 border-emerald-100 text-slate-950 scale-125 shadow-emerald-500/40' 
                      : 'bg-slate-900 border-emerald-500/80 text-emerald-400'
                  }`}>
                    {player.name.substring(0, 2).toUpperCase()}
                  </div>

                  {/* Player Name Tag */}
                  <div className="absolute left-1/2 -translate-x-1/2 mt-1 whitespace-nowrap bg-slate-950/80 text-[10px] text-slate-300 px-1.5 py-0.5 rounded border border-slate-800/40">
                    {player.name.split(' ').pop()}
                  </div>

                  {/* Player Hover Information Tooltip */}
                  {isHovered && (
                    <div className="absolute left-10 top-0 -translate-y-1/3 w-64 bg-slate-950/95 border border-slate-800 rounded-lg p-3 shadow-2xl z-30 pointer-events-none backdrop-blur-md">
                      <div className="font-bold text-sm text-slate-100">{player.name}</div>
                      <div className="text-xs text-emerald-400 font-medium mb-2">{player.position}</div>
                      <div className="text-[11px] text-slate-400 mb-1">
                        <strong className="text-slate-300 font-medium">Club:</strong> {player.club}
                      </div>
                      
                      <div className="mt-2 pt-2 border-t border-slate-800/60 font-mono text-[10px]">
                        <div className="text-slate-500 uppercase tracking-wider mb-1 text-[9px]">Resolved IDs</div>
                        <div className="flex justify-between text-slate-400">
                          <span>StatsBomb:</span>
                          <span className="text-emerald-400/90">{player.resolvedIds?.statsbomb}</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>FBref:</span>
                          <span className="text-emerald-400/90">{player.resolvedIds?.fbref}</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Transfermarkt:</span>
                          <span className="text-emerald-400/90">{player.resolvedIds?.transfermarkt}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
