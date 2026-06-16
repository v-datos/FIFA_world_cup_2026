import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';

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

interface BracketRound {
  name: string;
  matches: BracketMatch[];
}

interface BracketData {
  tournament?: string;
  groups: Group[];
  // Live API shape: flat keys, populated only when knockout games exist.
  r32?: BracketMatch[];
  r16?: BracketMatch[];
  qf?: BracketMatch[];
  sf?: BracketMatch[];
  final?: BracketMatch[];
  third?: BracketMatch[];
  // Seed / fallback shape: the same structure the Streamlit board consumes.
  rounds?: BracketRound[];
  third_place?: BracketMatch | null;
}

export const StandingsTab: React.FC<StandingsTabProps> = ({ serverUrl, lang }) => {
  const [data, setData] = useState<BracketData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

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

  const wrapRef = useRef<HTMLDivElement>(null);
  const [nativeFs, setNativeFs] = useState(false);
  const [overlay, setOverlay] = useState(false);
  const isFullscreen = nativeFs || overlay;

  useEffect(() => {
    const onFsChange = () => setNativeFs(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', onFsChange);
    return () => document.removeEventListener('fullscreenchange', onFsChange);
  }, []);

  // CSS-overlay fallback (used when the native Fullscreen API is unavailable,
  // e.g. inside an iframe without allowfullscreen). Esc exits it.
  useEffect(() => {
    if (!overlay) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOverlay(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [overlay]);

  const toggleFullscreen = () => {
    const el = wrapRef.current;
    if (!el) return;
    if (document.fullscreenElement) { document.exitFullscreen?.(); return; }
    if (overlay) { setOverlay(false); return; }
    if (el.requestFullscreen) {
      Promise.resolve(el.requestFullscreen()).catch(() => setOverlay(true));
    } else {
      setOverlay(true);
    }
  };

  // Scale the fixed-size board down to fit the available area so the ENTIRE
  // bracket is always visible (never cut off). In fullscreen we also fit height.
  const fitRef = useRef<HTMLDivElement>(null);
  const boardRef = useRef<HTMLDivElement>(null);
  const [fit, setFit] = useState({ scale: 1, w: 0, h: 0 });

  useLayoutEffect(() => {
    const recompute = () => {
      const board = boardRef.current;
      const area = fitRef.current;
      if (!board || !area) return;
      const bw = board.offsetWidth || 1720;
      const bh = board.offsetHeight || 980;
      const availW = area.clientWidth;
      const availH = isFullscreen ? area.clientHeight : Infinity;
      const scale = Math.min(1, availW / bw, availH / bh);
      setFit((prev) =>
        prev.scale === scale && prev.w === bw * scale && prev.h === bh * scale
          ? prev
          : { scale, w: bw * scale, h: bh * scale }
      );
    };
    recompute();
    const ro = new ResizeObserver(recompute);
    if (fitRef.current) ro.observe(fitRef.current);
    window.addEventListener('resize', recompute);
    return () => { ro.disconnect(); window.removeEventListener('resize', recompute); };
  }, [isFullscreen, data, lang]);

  if (loading || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] gap-3">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium text-slate-400 font-mono">
          {lang === 'Español' ? 'Cargando clasificaciones y llaves...' : 'Fetching standings and bracket...'}
        </span>
      </div>
    );
  }

  // Prefer the live flat keys; fall back to the seed nested `rounds[]` shape
  // (the same structure the Streamlit painter's-tape board consumes) so the
  // full bracket always renders even before knockout games are seeded live.
  const rounds = data.rounds || [];
  const roundMatches = (i: number) => rounds[i]?.matches || [];
  const r32 = data.r32 || roundMatches(0);
  const r16 = data.r16 || roundMatches(1);
  const qf = data.qf || roundMatches(2);
  const sf = data.sf || roundMatches(3);
  const finalMatch =
    data.final?.[0] ||
    roundMatches(4)[0] || { id: 'f_104', team1: '???', team2: '???', score1: null, score2: null, winner: null };
  const thirdPlaceMatch = data.third?.[0] || data.third_place || null;

  const translateGroup = (gName: string) => {
    if (lang === 'English') return gName;
    return gName.replace('Group ', 'GRUPO ');
  };

  const renderGroupCard = (group: Group, idx: number) => {
    const gName = translateGroup(group.name);
    const standings = group.standings || [];
    const rotation = -1.5 + (idx % 3) * 1.2;

    return (
      <div 
        key={idx} 
        className="group-card flex gap-1 items-stretch relative"
        style={{ transform: `rotate(${rotation}deg)` }}
      >
        {/* Main Teams Box */}
        <div className="group-teams-box">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className="group-header">{gName.toUpperCase()}</div>
          {standings.map((s, sidx) => (
            <div key={sidx} className="group-team" title={s.team}>
              {s.team.toUpperCase()}
            </div>
          ))}
        </div>

        {/* P Strip */}
        <div className="group-stat-strip">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className="group-stat-header">{lang === 'Español' ? 'J' : 'P'}</div>
          {standings.map((s, sidx) => (
            <div key={sidx} className="group-stat-val font-mono">{s.p}</div>
          ))}
        </div>

        {/* W Strip */}
        <div className="group-stat-strip">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className="group-stat-header">{lang === 'Español' ? 'G' : 'W'}</div>
          {standings.map((s, sidx) => (
            <div key={sidx} className="group-stat-val font-mono">{s.w}</div>
          ))}
        </div>

        {/* D Strip */}
        <div className="group-stat-strip">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className="group-stat-header">{lang === 'Español' ? 'E' : 'D'}</div>
          {standings.map((s, sidx) => (
            <div key={sidx} className="group-stat-val font-mono">{s.d}</div>
          ))}
        </div>

        {/* L Strip */}
        <div className="group-stat-strip">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className="group-stat-header">{lang === 'Español' ? 'P' : 'L'}</div>
          {standings.map((s, sidx) => (
            <div key={sidx} className="group-stat-val font-mono">{s.l}</div>
          ))}
        </div>

        {/* GD Strip */}
        <div className="group-stat-strip">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className="group-stat-header">+/-</div>
          {standings.map((s, sidx) => {
            const gdVal = s.gd > 0 ? `+${s.gd}` : s.gd;
            return (
              <div key={sidx} className="group-stat-val font-mono">{gdVal}</div>
            );
          })}
        </div>

        {/* Pts Strip */}
        <div className="group-stat-strip highlight-pts">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className="group-stat-header">Pts</div>
          {standings.map((s, sidx) => (
            <div key={sidx} className="group-stat-val font-bold font-mono">{s.pts}</div>
          ))}
        </div>
      </div>
    );
  };

  const renderMatchupCell = (
    match: BracketMatch | undefined,
    roundClass: string,
    hasPrevLine = false,
    hasNextLine = false,
    isLeftHalf = true
  ) => {
    const t1 = match?.team1 || '???';
    const t2 = match?.team2 || '???';
    const s1 = match?.score1;
    const s2 = match?.score2;
    const w = match?.winner;

    const isT1Winner = w === t1 && t1 !== '???';
    const isT2Winner = w === t2 && t2 !== '???';

    return (
      <div className={`matchup ${roundClass} flex flex-col justify-center items-center relative z-10`}>
        {/* Team 1 Tape */}
        <div className="team-tape-wrapper relative">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className={`team-tape flex justify-between items-center px-2 py-0.5 ${isT1Winner ? 'winner' : ''}`}>
            <span className="truncate max-w-[85px]">{t1.toUpperCase()}</span>
            {s1 !== null && s1 !== undefined && (
              <span className="font-bold font-mono ml-1">{s1}</span>
            )}
          </div>
        </div>

        {/* Team 2 Tape */}
        <div className="team-tape-wrapper relative mt-1">
          <div className="tape-corner-left"></div>
          <div className="tape-corner-right"></div>
          <div className={`team-tape flex justify-between items-center px-2 py-0.5 ${isT2Winner ? 'winner' : ''}`}>
            <span className="truncate max-w-[85px]">{t2.toUpperCase()}</span>
            {s2 !== null && s2 !== undefined && (
              <span className="font-bold font-mono ml-1">{s2}</span>
            )}
          </div>
        </div>

        {/* Connectors */}
        {isLeftHalf ? (
          <>
            {hasNextLine && (
              <>
                <div className="bracket-line-horizontal"></div>
                <div className="bracket-line-vertical"></div>
              </>
            )}
            {hasPrevLine && <div className="bracket-line-horizontal-left"></div>}
          </>
        ) : (
          <>
            {hasNextLine && (
              <>
                <div className="bracket-line-horizontal"></div>
                <div className="bracket-line-vertical"></div>
              </>
            )}
            {hasPrevLine && <div className="bracket-line-horizontal-right"></div>}
          </>
        )}
      </div>
    );
  };

  return (
    <div className="w-full select-none relative">
      {/* CSS Injected Styles for the Wood Panel and Tape Effect */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap');

        .board-wrap {
          width: 100%;
        }

        .board-wrap:fullscreen,
        .board-wrap.overlay {
          background-color: #11161f;
          padding: 16px;
          overflow: auto;
          display: flex;
          flex-direction: column;
        }

        .board-wrap.overlay {
          position: fixed;
          inset: 0;
          z-index: 60;
        }

        .bracket-fit-area {
          width: 100%;
          display: flex;
          justify-content: center;
          overflow: hidden;
        }

        .board-wrap:fullscreen .bracket-fit-area,
        .board-wrap.overlay .bracket-fit-area {
          flex: 1 1 auto;
          align-items: center;
        }

        .bracket-fit-inner {
          position: relative;
          overflow: hidden;
        }

        .bracket-board {
          background-color: #b1814a;
          background-image: 
            radial-gradient(circle at 50% 50%, rgba(255,255,255,0.06) 0%, rgba(0,0,0,0.25) 100%),
            repeating-linear-gradient(0deg, rgba(0,0,0,0.015) 0px, rgba(0,0,0,0.015) 2px, transparent 2px, transparent 24px),
            repeating-linear-gradient(90deg, rgba(0,0,0,0.015) 0px, rgba(0,0,0,0.015) 2px, transparent 2px, transparent 24px);
          padding: 70px 20px 30px 20px;
          border-radius: 1rem;
          min-height: 980px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          box-shadow: inset 0 0 80px rgba(0,0,0,0.5), 0 10px 30px rgba(0,0,0,0.3);
          font-family: 'Permanent Marker', cursive;
          position: absolute;
          top: 0;
          left: 0;
          transform-origin: top left;
          overflow: visible;
          box-sizing: border-box;
          min-width: 1720px;
        }

        .left-groups, .right-groups {
          display: flex;
          flex-direction: column;
          justify-content: space-around;
          height: 860px;
          width: 275px;
          z-index: 5;
        }

        .left-bracket, .right-bracket {
          display: flex;
          justify-content: space-around;
          align-items: center;
          height: 860px;
          width: 440px;
        }

        .bracket-round {
          display: flex;
          flex-direction: column;
          justify-content: space-around;
          height: 100%;
          width: 100px;
          position: relative;
        }

        .center-column {
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 860px;
          width: 130px;
          z-index: 5;
          position: relative;
        }

        /* Tape Styles */
        .group-teams-box {
          background-color: #2b77c8;
          color: #0d0d0d;
          padding: 8px 10px;
          border-radius: 2px;
          box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
          width: 100px;
          font-size: 11px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          position: relative;
        }

        .group-header {
          border-bottom: 2px dashed rgba(0,0,0,0.18);
          padding-bottom: 3px;
          margin-bottom: 4px;
          font-weight: bold;
          text-align: center;
          letter-spacing: 0.5px;
        }

        .group-team {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          line-height: 1.4;
          text-transform: uppercase;
        }

        .group-stat-strip {
          background-color: #2e7cd2;
          color: #0d0d0d;
          padding: 8px 2px;
          border-radius: 2px;
          box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
          width: 23px;
          font-size: 10px;
          text-align: center;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          align-items: center;
          position: relative;
        }

        .group-stat-header {
          border-bottom: 2px dashed rgba(0,0,0,0.18);
          padding-bottom: 3px;
          margin-bottom: 4px;
          width: 100%;
          font-weight: bold;
        }

        .group-stat-val {
          line-height: 1.4;
        }

        .group-stat-strip.highlight-pts {
          background-color: #1e67b3;
          color: #ffffff;
        }

        .group-stat-strip.highlight-pts .group-stat-header {
          border-bottom: 2px dashed rgba(255,255,255,0.25);
        }

        /* Matchup cards */
        .matchup {
          height: 80px;
          z-index: 3;
        }

        .team-tape {
          background-color: #2b77c8;
          color: #0d0d0d;
          font-size: 11px;
          width: 92px;
          box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
          position: relative;
          transform: rotate(-1deg);
          clip-path: polygon(1% 0, 99% 2%, 98% 97%, 2% 98%);
        }

        .matchup:nth-child(even) .team-tape {
          transform: rotate(1.2deg);
          clip-path: polygon(2% 1%, 98% 0, 99% 99%, 1% 96%);
        }

        .team-tape.winner {
          background-color: #164f8f;
          color: #ffffff;
          font-weight: bold;
          text-shadow: 1px 1px 1px rgba(0,0,0,0.4);
        }

        /* Champion Box */
        .champion-box {
          display: flex;
          flex-direction: column;
          align-items: center;
          margin-bottom: 30px;
          position: relative;
        }

        .champion-tape {
          background-color: #f3c734;
          color: #0d0d0d;
          font-size: 14px;
          padding: 8px 18px;
          box-shadow: 3px 3px 6px rgba(0,0,0,0.35);
          transform: rotate(-2.5deg);
          text-align: center;
          border-radius: 2px;
          clip-path: polygon(2% 0, 98% 3%, 100% 97%, 0 100%);
          margin-bottom: 6px;
        }

        .champion-label {
          font-size: 10px;
          color: rgba(255,255,255,0.85);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }

        .final-label {
          background-color: rgba(244, 230, 181, 0.95);
          color: #0d0d0d;
          font-size: 10px;
          padding: 2px 8px;
          box-shadow: 1px 1px 3px rgba(0,0,0,0.25);
          transform: rotate(1.5deg);
          margin-bottom: 20px;
        }

        /* Connecting Lines (Masking Tape) */
        .bracket-line-horizontal {
          background-color: #eae6cf;
          height: 6px;
          width: 25px;
          position: absolute;
          box-shadow: 1px 1px 3px rgba(0,0,0,0.18);
          z-index: 1;
        }

        .left-bracket .bracket-line-horizontal {
          right: -25px;
        }

        .right-bracket .bracket-line-horizontal {
          left: -25px;
        }

        .bracket-line-horizontal-left {
          background-color: #eae6cf;
          height: 6px;
          width: 25px;
          position: absolute;
          left: -25px;
          box-shadow: 1px 1px 3px rgba(0,0,0,0.18);
          z-index: 1;
        }

        .bracket-line-horizontal-right {
          background-color: #eae6cf;
          height: 6px;
          width: 25px;
          position: absolute;
          right: -25px;
          box-shadow: 1px 1px 3px rgba(0,0,0,0.18);
          z-index: 1;
        }

        .bracket-line-vertical {
          background-color: #eae6cf;
          width: 6px;
          position: absolute;
          box-shadow: 1px 1px 3px rgba(0,0,0,0.18);
          z-index: 1;
        }

        .left-bracket .bracket-line-vertical {
          right: -25px;
        }

        .right-bracket .bracket-line-vertical {
          left: -25px;
        }

        .matchup:nth-child(odd) .bracket-line-vertical {
          top: 50%;
        }

        .matchup:nth-child(even) .bracket-line-vertical {
          bottom: 50%;
        }

        /* Heights mapping to rounds */
        .r32-matchup .bracket-line-vertical {
          height: 55px;
        }
        .r16-matchup .bracket-line-vertical {
          height: 108px;
        }
        .qf-matchup .bracket-line-vertical {
          height: 215px;
        }

        /* Corner Tape Pieces */
        .tape-corner-left {
          position: absolute;
          width: 14px;
          height: 5px;
          background-color: rgba(244, 230, 181, 0.88);
          top: -3px;
          left: -5px;
          transform: rotate(-30deg);
          z-index: 6;
          box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }

        .tape-corner-right {
          position: absolute;
          width: 14px;
          height: 5px;
          background-color: rgba(244, 230, 181, 0.88);
          bottom: -3px;
          right: -5px;
          transform: rotate(25deg);
          z-index: 6;
          box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }

        .board-title {
          position: absolute;
          top: 20px;
          left: 50%;
          transform: translateX(-50%) rotate(-1deg);
          background-color: rgba(244, 230, 181, 0.98);
          color: #0d0d0d;
          font-size: 24px;
          padding: 6px 36px;
          box-shadow: 2px 2px 6px rgba(0,0,0,0.35);
          z-index: 10;
          text-transform: uppercase;
          clip-path: polygon(1% 0, 99% 1%, 98% 98%, 0 99%);
        }

        .board-title::before {
          content: "";
          position: absolute;
          width: 35px;
          height: 12px;
          background-color: rgba(244, 230, 181, 0.85);
          top: -8px;
          left: -20px;
          transform: rotate(-35deg);
        }

        .board-title::after {
          content: "";
          position: absolute;
          width: 35px;
          height: 12px;
          background-color: rgba(244, 230, 181, 0.85);
          bottom: -8px;
          right: -20px;
          transform: rotate(-30deg);
        }
      `}</style>

      {/* Board wrapper — target for native fullscreen / overlay fallback */}
      <div ref={wrapRef} className={`board-wrap${overlay ? ' overlay' : ''}`}>
        {/* Toolbar: full-screen toggle + scroll hint */}
        <div className="flex items-center justify-end gap-3 mb-3">
          <span className="text-[11px] text-slate-500 font-mono hidden md:inline">
            {lang === 'Español' ? 'Pantalla completa para ampliar' : 'Use Full Screen for a larger view'}
          </span>
          <button
            onClick={toggleFullscreen}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            {isFullscreen
              ? (lang === 'Español' ? 'Salir' : 'Exit Full Screen')
              : (lang === 'Español' ? 'Pantalla Completa' : 'Full Screen')}
          </button>
        </div>

        {/* Wood-board bracket — scaled to fit so the whole thing is always visible */}
        <div ref={fitRef} className="bracket-fit-area">
          <div className="bracket-fit-inner" style={{ width: fit.w || undefined, height: fit.h || undefined }}>
            <div ref={boardRef} className="bracket-board" style={{ transform: `scale(${fit.scale})` }}>
        {/* Title */}
        <div className="board-title">
          {lang === 'Español' ? 'COPA MUNDIAL 2026' : (data.tournament || 'World Cup 2026')}
        </div>

        {/* Left Side Groups (A to F) */}
        <div className="left-groups">
          {data.groups.slice(0, 6).map((g, idx) => renderGroupCard(g, idx))}
        </div>

        {/* Left Bracket Round of 32 down to Semifinals */}
        <div className="left-bracket">
          {/* Round of 32 Column (8 matches) */}
          <div className="bracket-round">
            {r32.slice(0, 8).map((m) =>
              renderMatchupCell(m, 'r32-matchup', false, true, true)
            )}
          </div>

          {/* Round of 16 Column (4 matches) */}
          <div className="bracket-round">
            {r16.slice(0, 4).map((m) =>
              renderMatchupCell(m, 'r16-matchup', true, true, true)
            )}
          </div>

          {/* Quarterfinals Column (2 matches) */}
          <div className="bracket-round">
            {qf.slice(0, 2).map((m) =>
              renderMatchupCell(m, 'qf-matchup', true, true, true)
            )}
          </div>

          {/* Semifinals Column (1 match) */}
          <div className="bracket-round">
            {sf.slice(0, 1).map((m) =>
              renderMatchupCell(m, 'sf-matchup', true, true, true)
            )}
          </div>
        </div>

        {/* Center Champion & Final Box */}
        <div className="center-column">
          {/* Champion display */}
          <div className="champion-box">
            <div className="tape-corner-left" style={{ width: '22px', height: '8px', top: -5, left: -10 }}></div>
            <div className="tape-corner-right" style={{ width: '22px', height: '8px', bottom: -5, right: -10 }}></div>
            <div className="champion-tape">
              {(finalMatch.winner || '???').toUpperCase()}
            </div>
            <div className="champion-label">
              {lang === 'Español' ? 'Campeón del Mundo' : 'World Cup Champion'}
            </div>
          </div>

          {/* Final Matchup Tag */}
          <div className="final-label">
            {lang === 'Español' ? 'FINAL DEL MUNDIAL' : 'WORLD CUP FINAL'}
          </div>

          {/* Final Match Up Cells */}
          <div className="matchup final-matchup flex flex-col justify-center items-center relative z-10" style={{ height: '90px' }}>
            <div className="bracket-line-horizontal-left" style={{ width: '45px', left: '-45px' }}></div>
            <div className="bracket-line-horizontal-right" style={{ width: '45px', right: '-45px' }}></div>

            <div className="team-tape-wrapper relative">
              <div className="tape-corner-left"></div>
              <div className="tape-corner-right"></div>
              <div className={`team-tape flex justify-between items-center px-2.5 py-1 ${finalMatch.winner === finalMatch.team1 && finalMatch.team1 !== '???' ? 'winner' : ''}`} style={{ width: '105px', fontSize: '12px' }}>
                <span className="truncate max-w-[85px]">{finalMatch.team1.toUpperCase()}</span>
                {finalMatch.score1 !== null && <span>{finalMatch.score1}</span>}
              </div>
            </div>

            <div className="team-tape-wrapper relative mt-1.5">
              <div className="tape-corner-left"></div>
              <div className="tape-corner-right"></div>
              <div className={`team-tape flex justify-between items-center px-2.5 py-1 ${finalMatch.winner === finalMatch.team2 && finalMatch.team2 !== '???' ? 'winner' : ''}`} style={{ width: '105px', fontSize: '12px' }}>
                <span className="truncate max-w-[85px]">{finalMatch.team2.toUpperCase()}</span>
                {finalMatch.score2 !== null && <span>{finalMatch.score2}</span>}
              </div>
            </div>
          </div>

          {/* Third Place Matchup Display */}
          {thirdPlaceMatch && (
            <div className="mt-8 pt-5 border-t-2 border-dashed border-black/15 w-full flex flex-col items-center">
              <div className="final-label" style={{ fontSize: '9px', padding: '1px 6px', marginBottom: '8px' }}>
                {lang === 'Español' ? 'TERCER PUESTO' : 'THIRD PLACE PLAYOFF'}
              </div>
              <div className="matchup third-place-matchup flex flex-col justify-center items-center relative z-10">
                <div className="team-tape-wrapper relative">
                  <div className="tape-corner-left" style={{ width: '10px', height: '4px' }}></div>
                  <div className="tape-corner-right" style={{ width: '10px', height: '4px' }}></div>
                  <div className={`team-tape flex justify-between items-center px-2 py-0.5 ${thirdPlaceMatch.winner === thirdPlaceMatch.team1 && thirdPlaceMatch.team1 !== '???' ? 'winner' : ''}`} style={{ width: '80px', fontSize: '9px' }}>
                    <span className="truncate max-w-[65px]">{thirdPlaceMatch.team1.toUpperCase()}</span>
                    {thirdPlaceMatch.score1 !== null && <span>{thirdPlaceMatch.score1}</span>}
                  </div>
                </div>

                <div className="team-tape-wrapper relative mt-1">
                  <div className="tape-corner-left" style={{ width: '10px', height: '4px' }}></div>
                  <div className="tape-corner-right" style={{ width: '10px', height: '4px' }}></div>
                  <div className={`team-tape flex justify-between items-center px-2 py-0.5 ${thirdPlaceMatch.winner === thirdPlaceMatch.team2 && thirdPlaceMatch.team2 !== '???' ? 'winner' : ''}`} style={{ width: '80px', fontSize: '9px' }}>
                    <span className="truncate max-w-[65px]">{thirdPlaceMatch.team2.toUpperCase()}</span>
                    {thirdPlaceMatch.score2 !== null && <span>{thirdPlaceMatch.score2}</span>}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Bracket Round of 32 down to Semifinals */}
        <div className="right-bracket">
          {/* Semifinals Column (1 match) */}
          <div className="bracket-round">
            {sf.slice(1, 2).map((m) =>
              renderMatchupCell(m, 'sf-matchup', true, true, false)
            )}
          </div>

          {/* Quarterfinals Column (2 matches) */}
          <div className="bracket-round">
            {qf.slice(2, 4).map((m) =>
              renderMatchupCell(m, 'qf-matchup', true, true, false)
            )}
          </div>

          {/* Round of 16 Column (4 matches) */}
          <div className="bracket-round">
            {r16.slice(4, 8).map((m) =>
              renderMatchupCell(m, 'r16-matchup', true, true, false)
            )}
          </div>

          {/* Round of 32 Column (8 matches) */}
          <div className="bracket-round">
            {r32.slice(8, 16).map((m) =>
              renderMatchupCell(m, 'r32-matchup', false, true, false)
            )}
          </div>
        </div>

        {/* Right Side Groups (G to L) */}
        <div className="right-groups">
          {data.groups.slice(6, 12).map((g, idx) => renderGroupCard(g, idx + 6))}
        </div>
        </div>{/* .bracket-board */}
          </div>{/* .bracket-fit-inner */}
        </div>{/* .bracket-fit-area */}
      </div>{/* .board-wrap */}
    </div>
  );
};
