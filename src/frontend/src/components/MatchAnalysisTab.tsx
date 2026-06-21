import React, { useState, useEffect } from 'react';
import { InteractivePitch } from './InteractivePitch';
import { MatchPredictionGraph } from './MatchPredictionGraph';
import { TeamRadarComparison } from './TeamRadarComparison';
import { SquadStyleComparison } from './SquadStyleComparison';
import { MonteCarloProjections } from './MonteCarloProjections';
import { BriefingFreshnessBadge, type BriefingFreshnessStatus } from './BriefingFreshnessBadge';
import { ShieldAlert, Award, FileText, Image as ImageIcon } from 'lucide-react';
import { getFlag, getLastStanding } from '../lib/teamData';
import { normalizeTeamName, teamSlug } from '../lib/teamIdentity';

interface Match {
  id: string;
  team1: string;
  team2: string;
  date: string;
  time: string;
  venue: string;
  stage: string;
  lifecycle?: 'finished' | 'today' | 'upcoming' | 'unresolved' | 'archived';
}

interface MatchAnalysisTabProps {
  matches: Match[];
  selectedMatchId: string | null;
  setSelectedMatchId: (matchId: string | null) => void;
  activeDate: string;
  lang: string;
  serverUrl: string;
}

type MetricValue = number | string | null | undefined;
type TeamMetricRecord = Record<string, MetricValue>;
type QualityRecord = {
  status?: string;
  source_label?: string;
  message?: string;
  freshness_state?: string;
  checked_at_utc?: string;
  generated_at_utc?: string;
};
type RadarQualityRecord = QualityRecord & {
  missing_fields?: Record<string, string[]>;
};
type TeamMetricQualityRecord = QualityRecord & {
  missing_fields?: unknown;
  field_sources?: Record<string, unknown>;
};

interface SummaryMetadata {
  match_id: string;
  team1: string;
  team2: string;
  date: string;
  time: string;
  venue: string;
  stage: string;
}

interface SummaryPayload {
  metadata: SummaryMetadata;
  ai_summary: {
    key_headline: string;
    injuries: Record<string, string[]>;
    confirmed_tactics: Record<string, {
      formation?: string;
      philosophy?: string;
      manager?: string;
    }>;
    tactical_insights: string[];
  };
  rosters?: Record<string, string[]>;
  player_clubs?: Record<string, string>;
  briefing_status?: QualityRecord;
}

interface MetricsPayload {
  dixon_coles_forecast?: {
    team1_win?: number | null;
    draw?: number | null;
    team2_win?: number | null;
    confidence?: number | null;
  };
  score_probabilities?: Array<{ score: string; probability: number }>;
  team_metrics?: Record<string, TeamMetricRecord>;
  team_metric_sources?: Record<string, unknown>;
  squad_style_sources?: Record<string, unknown>;
  viz_proxies?: Record<string, string>;
  elo_ratings?: Record<string, number | null>;
  monte_carlo_projections?: Record<string, Record<string, MetricValue>>;
  data_quality?: {
    forecast?: QualityRecord;
    score_probabilities?: QualityRecord;
    radar_metrics?: RadarQualityRecord;
    elo_ratings?: Record<string, TeamMetricQualityRecord>;
    monte_carlo_projections?: QualityRecord;
    team_metrics?: Record<string, TeamMetricQualityRecord>;
  };
}

interface BriefingSourceRecord {
  label?: string;
  source_label?: string;
  checked_at_utc?: string;
}

interface BriefingPayload {
  freshness_state?: string;
  source_label?: string;
  message?: string;
  generated_at_utc?: string;
  checked_at_utc?: string;
  metadata?: {
    freshness?: string;
    freshness_state?: string;
    generated_at_utc?: string;
    valid_until_utc?: string;
  };
  data_quality?: {
    freshness_state?: string;
    warnings?: string[];
    blocked_reasons?: string[];
  };
  sources?: BriefingSourceRecord[];
  briefing_status?: QualityRecord;
}

type BriefingRouteStatus = BriefingFreshnessStatus & {
  http_status?: number;
};

const firstText = (...values: Array<unknown>): string | undefined => (
  values.find((value): value is string => typeof value === 'string' && value.trim().length > 0)?.trim()
);

const chooseSourceLabel = (sources?: BriefingSourceRecord[]): string | undefined => {
  if (!sources || sources.length === 0) return undefined;
  const labels = sources
    .map((source) => source.source_label || source.label)
    .filter((label): label is string => Boolean(label));
  return labels.includes('web_researched') ? 'web_researched' : labels[0];
};

const normalizeBriefingStatus = (
  summaryStatus: QualityRecord | undefined,
  briefingData: BriefingPayload | null,
  routeStatus: BriefingRouteStatus | null,
): BriefingFreshnessStatus => {
  if (briefingData) {
    const freshness = firstText(
      briefingData.freshness_state,
      briefingData.data_quality?.freshness_state,
      briefingData.metadata?.freshness,
      briefingData.metadata?.freshness_state,
      briefingData.briefing_status?.freshness_state,
    ) || 'fresh';
    const generatedAt = firstText(
      briefingData.generated_at_utc,
      briefingData.metadata?.generated_at_utc,
      briefingData.briefing_status?.generated_at_utc,
    );
    const checkedAt = firstText(
      briefingData.checked_at_utc,
      briefingData.briefing_status?.checked_at_utc,
      generatedAt,
      ...(briefingData.sources || []).map((source) => source.checked_at_utc),
    );

    return {
      freshness_state: freshness,
      source_label: chooseSourceLabel(briefingData.sources) || briefingData.source_label || briefingData.briefing_status?.source_label || 'static_curated',
      message: briefingData.message || briefingData.briefing_status?.message || (
        freshness === 'fresh'
          ? 'Last-minute briefing artifact is available.'
          : 'Briefing artifact is available but not fresh.'
      ),
      generated_at_utc: generatedAt,
      valid_until_utc: briefingData.metadata?.valid_until_utc,
      checked_at_utc: checkedAt,
      status_origin: 'briefing_endpoint',
      source_count: briefingData.sources?.length,
      warnings: briefingData.data_quality?.warnings,
      blocked_reasons: briefingData.data_quality?.blocked_reasons,
    };
  }

  if (routeStatus?.freshness_state === 'missing' && summaryStatus?.freshness_state) {
    return {
      ...summaryStatus,
      status_origin: 'summary_fallback',
    };
  }

  if (routeStatus?.freshness_state) return routeStatus;

  if (summaryStatus?.freshness_state) {
    return {
      ...summaryStatus,
      status_origin: 'summary_fallback',
    };
  }

  return {
    freshness_state: 'missing',
    source_label: 'missing',
    message: 'No briefing status is available for this fixture.',
    status_origin: 'frontend_fallback',
  };
};

export const MatchAnalysisTab: React.FC<MatchAnalysisTabProps> = ({
  matches,
  selectedMatchId,
  setSelectedMatchId,
  activeDate,
  lang,
  serverUrl,
}) => {
  const [summaryData, setSummaryData] = useState<SummaryPayload | null>(null);
  const [metricsData, setMetricsData] = useState<MetricsPayload | null>(null);
  const [briefingData, setBriefingData] = useState<BriefingPayload | null>(null);
  const [briefingRouteStatus, setBriefingRouteStatus] = useState<BriefingRouteStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeVizTab, setActiveVizTab] = useState<string>('momentum');

  const dropdownMatches = matches.filter((match) => match.lifecycle === 'today');

  // If the active selection is finished/future, snap back to the current day.
  useEffect(() => {
    if (dropdownMatches.length === 0) {
      if (selectedMatchId) setSelectedMatchId(null);
      return;
    }
    if (!dropdownMatches.some((m) => m.id === selectedMatchId)) {
      setSelectedMatchId(dropdownMatches[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matches, selectedMatchId]);

  // Roster listing from app.py
  const ROSTERS: Record<string, string[]> = {
    "Netherlands": ["Bart Verbruggen", "Denzel Dumfries", "Virgil van Dijk", "Stefan de Vrij", "Nathan Ake", "Jerdy Schouten", "Tijjani Reijnders", "Joey Veerman", "Xavi Simons", "Memphis Depay", "Cody Gakpo"],
    "Japan": ["Zion Suzuki", "Yukinari Sugawara", "Ko Itakura", "Koki Machida", "Keito Nakamura", "Wataru Endo", "Hidemasa Morita", "Ritsu Doan", "Takumi Minamino", "Takefusa Kubo", "Ayase Ueda"],
    "France": ["Mike Maignan", "Jules Kounde", "William Saliba", "Dayot Upamecano", "Theo Hernandez", "Aurelien Tchouameni", "Adrien Rabiot", "Ousmane Dembele", "Michael Olise", "Desire Doue", "Kylian Mbappe"],
    "Senegal": ["Edouard Mendy", "El Hadji Malick Diouf", "Kalidou Koulibaly", "Moussa Niakhate", "Krepin Diatta", "Lamine Camara", "Pape Gueye", "Habib Diarra", "Iliman Ndiaye", "Sadio Mane", "Nicolas Jackson"],
    "Argentina": ["Emiliano Martinez", "Gonzalo Montiel", "Cristian Romero", "Lisandro Martinez", "Nicolas Tagliafico", "Rodrigo De Paul", "Enzo Fernandez", "Alexis Mac Allister", "Lionel Messi", "Lautaro Martinez", "Julian Alvarez"],
    "Algeria": ["Luca Zidane", "Rafik Belghali", "Aissa Mandi", "Jaouen Hadjam", "Rayan Ait-Nouri", "Nabil Bentaleb", "Hicham Boudaoui", "Fares Chaibi", "Mohamed Amoura", "Amine Gouiri", "Riyad Mahrez"],
    "Austria": ["Patrick Pentz", "Stefan Posch", "Kevin Danso", "Maximilian Wober", "Phillipp Mwene", "Nicolas Seiwald", "Marcel Sabitzer", "Konrad Laimer", "Christoph Baumgartner", "Patrick Wimmer", "Michael Gregoritsch"],
    "Norway": ["Orjan Nyland", "Julian Ryerson", "Kristoffer Ajer", "Torbjorn Heggem", "David Wolfe", "Sander Berge", "Fredrik Aursnes", "Martin Odegaard", "Alexander Sorloth", "Erling Haaland", "Antonio Nusa"],
    "Iraq": ["Jalal Hassan", "Hussein Ali", "Saad Natiq", "Rebin Sulaka", "Merchas Doski", "Amir Al-Ammari", "Zidane Iqbal", "Ibrahim Bayesh", "Ali Jasim", "Ali Al-Hamadi", "Aymen Hussein"],
    "Jordan": ["Yazeed Abulaila", "Abdallah Nasib", "Yazan Al-Arab", "Saleem Obaid", "Ehsan Haddad", "Nizar Al-Rashdan", "Noor Al-Rawabdeh", "Mohannad Abu Taha", "Musa Al-Taamari", "Ali Olwan", "Odeh Fakhoury"],
    "Portugal": ["Diogo Costa", "Joao Cancelo", "Ruben Dias", "Goncalo Inacio", "Nuno Mendes", "Vitinha", "Joao Neves", "Bernardo Silva", "Bruno Fernandes", "Rafael Leao", "Cristiano Ronaldo"],
    "DR Congo": ["Lionel Mpasi", "Gedeon Kalulu", "Chancel Mbemba", "Dylan Batubinsika", "Arthur Masuaku", "Samuel Moutoussamy", "Charles Pickel", "Theo Bongonda", "Gael Kakuta", "Yoane Wissa", "Cedric Bakambu"],
    "Uzbekistan": ["Utkir Yusupov", "Abdukodir Khusanov", "Rustam Ashurmatov", "Umar Eshmurodov", "Sherzod Nasrullaev", "Otabek Shukurov", "Odiljon Hamrobekov", "Abbosbek Fayzullaev", "Jaloliddin Masharipov", "Eldor Shomurodov", "Igor Sergeev"],
    "Colombia": ["Camilo Vargas", "Daniel Munoz", "Davinson Sanchez", "Jhon Lucumi", "Johan Mojica", "Richard Rios", "Jefferson Lerma", "Jhon Arias", "James Rodriguez", "Luis Diaz", "Luis Suarez"],
    "Spain": ["Unai Simon", "Marcos Llorente", "Pau Cubarsi", "Aymeric Laporte", "Marc Cucurella", "Rodri", "Pedri", "Fabian Ruiz", "Lamine Yamal", "Mikel Oyarzabal", "Nico Williams"],
    "Cape Verde": ["Vozinha", "Steven Moreira", "Logan Costa", "Roberto Lopes", "Joao Paulo", "Kevin Pina", "Jamiro Monteiro", "Deroy Duarte", "Ryan Mendes", "Bebé", "Jovane Cabral"],
    "Belgium": ["Thibaut Courtois", "Thomas Meunier", "Nathan Ngoy", "Brandon Mechele", "Timothy Castagne", "Amadou Onana", "Youri Tielemans", "Dodi Lukebakio", "Kevin De Bruyne", "Jeremy Doku", "Charles De Ketelaere"],
    "Egypt": ["Mohamed El Shenawy", "Mohamed Rabia", "Mohamed Abdelmonem", "Mohamed Hany", "Ahmed Fatouh", "Marwan Attia", "Hamdi Fathi", "Emam Ashour", "Mohamed Salah", "Omar Marmoush", "Zizo"],
    "Saudi Arabia": ["Mohammed Al-Owais", "Saud Abdulhamid", "Ali Lajami", "Ali Al-Bulaihi", "Yasser Al-Shahrani", "Faisal Al-Ghamdi", "Abdulelah Al-Malki", "Mohamed Kanno", "Salem Al-Dawsari", "Firas Al-Buraikan", "Saleh Al-Shehri"],
    "Uruguay": ["Sergio Rochet", "Nahitan Nandez", "Ronald Araujo", "Mathias Olivera", "Matias Vina", "Federico Valverde", "Manuel Ugarte", "Nicolas De La Cruz", "Facundo Pellistri", "Darwin Nunez", "Maximiliano Araujo"],
    "Iran": ["Alireza Beiranvand", "Ramin Rezaeian", "Hossein Kanaanizadegan", "Shojae Khalilzadeh", "Milad Mohammadi", "Saman Ghoddos", "Saeid Ezatolahi", "Alireza Jahanbakhsh", "Mehdi Ghayedi", "Mehdi Taremi", "Mehdi Torabi"],
    "New Zealand": ["Alex Paulsen", "Bill Tuiloma", "Michael Boxall", "Nando Pijnaker", "Liberato Cacace", "Joe Bell", "Matthew Garbett", "Sarpreet Singh", "Kosta Barbarouses", "Chris Wood", "Elijah Just"],
    "England": ["Jordan Pickford", "Reece James", "John Stones", "Marc Guehi", "Ezri Konsa", "Declan Rice", "Elliot Anderson", "Jude Bellingham", "Bukayo Saka", "Eberechi Eze", "Harry Kane"],
    "Croatia": ["Dominik Livakovic", "Josip Stanisic", "Josip Sutalo", "Mario Vuskovic", "Josko Gvardiol", "Luka Modric", "Mateo Kovacic", "Petar Sucic", "Martin Baturina", "Ivan Perisic", "Petar Musa"],
    "Ghana": ["Lawrence Ati-Zigi", "Alidu Seidu", "Alexander Djiku", "Mohammed Salisu", "Gideon Mensah", "Salis Abdul Samed", "Thomas Partey", "Ernest Nuamah", "Mohammed Kudus", "Jordan Ayew", "Inaki Williams"],
    "Panama": ["Orlando Mosquera", "Michael Murillo", "Jose Cordoba", "Edgardo Farina", "Eric Davis", "Adalberto Carrasquilla", "Cristian Martinez", "Edgar Barcenas", "Abdiel Ayarza", "Jose Luis Rodriguez", "Jose Fajardo"]
  };

  useEffect(() => {
    if (!selectedMatchId) return;
    let cancelled = false;

    const fetchData = async () => {
      setLoading(true);
      setSummaryData(null);
      setMetricsData(null);
      setBriefingData(null);
      setBriefingRouteStatus(null);
      try {
        const briefingRequest = fetch(`${serverUrl}/api/match/${selectedMatchId}/briefing`)
          .catch((err: unknown) => err);
        const [sumRes, metRes, briefingResult] = await Promise.all([
          fetch(`${serverUrl}/api/match/${selectedMatchId}/summary`),
          fetch(`${serverUrl}/api/match/${selectedMatchId}/metrics`),
          briefingRequest,
        ]);

        if (!sumRes.ok || !metRes.ok) {
          throw new Error(`Match analysis request failed: summary ${sumRes.status}, metrics ${metRes.status}`);
        }

        const [sumJson, metJson] = await Promise.all([
          sumRes.json(),
          metRes.json(),
        ]);

        let briefingJson: BriefingPayload | null = null;
        let routeStatus: BriefingRouteStatus | null = null;
        if (!(briefingResult instanceof Response)) {
          routeStatus = {
            freshness_state: 'blocked',
            source_label: 'blocked',
            message: 'Briefing endpoint could not be reached.',
            status_origin: 'briefing_endpoint',
          };
        } else if (briefingResult.ok) {
          try {
            briefingJson = await briefingResult.json();
          } catch (err) {
            routeStatus = {
              freshness_state: 'invalid',
              source_label: 'blocked',
              message: 'Briefing endpoint returned invalid JSON.',
              status_origin: 'briefing_endpoint',
            };
          }
        } else if (briefingResult.status === 404) {
          routeStatus = {
            freshness_state: 'missing',
            source_label: 'missing',
            message: 'No dedicated briefing artifact is available.',
            status_origin: 'briefing_endpoint',
            http_status: briefingResult.status,
          };
        } else {
          routeStatus = {
            freshness_state: 'blocked',
            source_label: 'blocked',
            message: `Briefing endpoint returned HTTP ${briefingResult.status}.`,
            status_origin: 'briefing_endpoint',
            http_status: briefingResult.status,
          };
        }

        if (!cancelled) {
          setSummaryData(sumJson);
          setMetricsData(metJson);
          setBriefingData(briefingJson);
          setBriefingRouteStatus(routeStatus);
        }
      } catch (err) {
        console.error("Failed to load match analytics data", err);
        if (!cancelled) {
          setBriefingRouteStatus({
            freshness_state: 'blocked',
            source_label: 'blocked',
            message: 'Match analysis data could not be loaded.',
            status_origin: 'frontend_fetch',
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    
    fetchData();

    return () => {
      cancelled = true;
    };
  }, [selectedMatchId, serverUrl]);

  if (!selectedMatchId) {
    return (
      <div className="glass-panel p-8 text-center text-slate-400">
        {lang === 'Español'
          ? `No hay partidos activos pendientes para ${activeDate || 'hoy'}.`
          : `No active unfinished fixtures for ${activeDate || 'today'}.`}
      </div>
    );
  }

  if (loading || !summaryData || !metricsData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] gap-3">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium text-slate-400">
          {lang === 'Español' ? 'Cargando análisis táctico...' : 'Compiling tactical analysis...'}
        </span>
      </div>
    );
  }

  const { team1, team2, date, time, venue, stage } = summaryData.metadata;
  const { key_headline, injuries, confirmed_tactics, tactical_insights } = summaryData.ai_summary;
  const forecast = metricsData.dixon_coles_forecast || {};
  const scoreProbs = metricsData.score_probabilities || [];
  const teamMetrics = metricsData.team_metrics || {};
  const vizProxies = metricsData.viz_proxies || {};
  const eloRatings = metricsData.elo_ratings || {};
  const monteCarlo = metricsData.monte_carlo_projections || {};
  const dataQuality = metricsData.data_quality || {};
  const briefingStatus = normalizeBriefingStatus(summaryData.briefing_status, briefingData, briefingRouteStatus);

  const normalizedTeam1 = normalizeTeamName(team1);
  const normalizedTeam2 = normalizeTeamName(team2);
  const cleanT1 = teamSlug(team1);
  const cleanT2 = teamSlug(team2);

  // Prefer source-backed rosters from the API (slug-keyed), then fall back to
  // the legacy local roster map for teams not yet in the lineup cache.
  const apiRosters = summaryData.rosters || {};
  const playerClubs = summaryData.player_clubs || {};
  const t1Roster = apiRosters[cleanT1] || ROSTERS[normalizedTeam1] || ROSTERS[team1] || ROSTERS[cleanT1] || [];
  const t2Roster = apiRosters[cleanT2] || ROSTERS[normalizedTeam2] || ROSTERS[team2] || ROSTERS[cleanT2] || [];

  const translateInjury = (inj: string) => {
    if (lang !== 'Español') return inj;
    if (inj === 'No major injuries reported.') return 'Sin lesiones graves reportadas.';
    if (inj === 'No verified baseline injury update is available yet.') return 'Sin actualización de lesiones disponible aún.';
    return inj
      .replace(/\(Concussion - Out\)/g, '(Conmoción cerebral - Baja)')
      .replace(/\(Groin Injury - Out\)/g, '(Lesión de ingle - Baja)')
      .replace(/\(Groin - Out\)/g, '(Lesión de ingle - Baja)')
      .replace(/\(Physical Issue - Doubtful\)/g, '(Problema físico - Duda)')
      .replace(/\(Minor Knock - Probable\)/g, '(Golpe menor - Probable)')
      .replace(/\(Medial Ligament - Out\)/g, '(Ligamento medial - Baja)')
      .replace(/\(Fitness - Doubtful\)/g, '(Estado físico - Duda)')
      .replace(/\(Thigh Strain - Doubtful\)/g, '(Distensión de muslo - Duda)')
      .replace(/\(Hamstring Tear - Out\)/g, '(Desgarro de isquiotibiales - Baja)')
      .replace(/\(Adductor Injury - Out\)/g, '(Lesión de aductores - Baja)')
      .replace(/\(Striker - Cleared to play\)/g, '(Delantero - Apto para jugar)')
      .replace(/\(Knee Injury - Out\)/g, '(Lesión de rodilla - Baja)')
      .replace(/\(Foot Injury - Out\)/g, '(Lesión de pie - Baja)')
      .replace(/\(Hamstring - Out\)/g, '(Isquiotibiales - Baja)');
  };

  const translateText = (text: string) => {
    // Basic translation helper for headers
    if (lang === 'English') return text;
    const map: Record<string, string> = {
      "Match Forecast": "Pronóstico de Partido",
      "Win Probability": "Probabilidades de Victoria",
      "Model Confidence": "Confianza del Modelo",
      "Top Exact Scores": "Marcadores Exactos Principales",
      "Key Match Insights": "Ideas Clave del Partido",
      "Injury Updates": "Actualización de Lesiones",
      "Team Tactics": "Tácticas de Equipos",
      "Squad Lineups": "Formaciones de Plantilla",
      "Formation": "Formación",
      "Philosophy": "Filosofía",
      "Manager": "Director Técnico",
      "Last Major Standing": "Última Participación Importante",
      "Coaching & Tactical Philosophies": "Cuerpo Técnico y Filosofías Tácticas",
    };
    return map[text] || text;
  };

  return (
    <div className="space-y-6">
      {/* Selector Dropdown Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/40 p-4 rounded-xl border border-slate-800/40">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>{getFlag(team1)} {team1}</span>
            <span className="text-xs text-slate-500 font-mono">VS</span>
            <span>{getFlag(team2)} {team2}</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            {stage} | {date} {time} | {venue}
          </p>
        </div>
        
        <select
          value={selectedMatchId}
          onChange={(e) => setSelectedMatchId(e.target.value)}
          className="bg-slate-950 text-slate-200 text-sm font-medium border border-slate-800 rounded-lg px-3.5 py-2 cursor-pointer focus:outline-none focus:border-emerald-500"
        >
          {dropdownMatches.map((m) => (
            <option key={m.id} value={m.id}>
              {getFlag(m.team1)} {m.team1} vs {getFlag(m.team2)} {m.team2}
            </option>
          ))}
        </select>
      </div>

      {/* Match Preview Headline */}
      <div className="glass-panel p-5 bg-gradient-to-r from-emerald-500/5 to-slate-950/20 border-l-4 border-l-emerald-500">
        <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest font-mono">
          AI Tactical Headline
        </span>
        <h3 className="text-lg font-bold text-slate-100 mt-1">
          {lang === 'Español' && key_headline ? 'Análisis: ' + key_headline : key_headline}
        </h3>
        <BriefingFreshnessBadge status={briefingStatus} lang={lang} />
      </div>

      {/* Match Outcome Probability (with integrated top exact scores) + Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MatchPredictionGraph
          team1={team1}
          team2={team2}
          probabilities={forecast}
          scoreProbs={scoreProbs}
          quality={dataQuality.forecast}
          scoreQuality={dataQuality.score_probabilities}
          lang={lang}
        />

        {/* Key Insights, Injuries & Last Major Standing */}
        <div className="glass-panel p-5 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-slate-200 mb-2 flex items-center gap-1.5">
              <FileText className="w-4.5 h-4.5 text-emerald-400" />
              <span>{translateText("Key Match Insights")}</span>
            </h4>
            <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
              {tactical_insights.map((insight: string, idx: number) => (
                <li key={idx} className="leading-relaxed">
                  {insight}
                </li>
              ))}
            </ul>
          </div>

          <div className="pt-3 border-t border-slate-800/60">
            <h4 className="text-sm font-bold text-slate-200 mb-2 flex items-center gap-1.5">
              <ShieldAlert className="w-4.5 h-4.5 text-emerald-400" />
              <span>{translateText("Injury Updates")}</span>
            </h4>
            <div className="space-y-1 text-[11px] text-slate-400 font-mono leading-relaxed">
              <div className="text-emerald-400 font-semibold">{getFlag(team1)} {team1}:</div>
              {injuries[cleanT1]?.map((inj: string, idx: number) => (
                <div key={idx}>• {translateInjury(inj)}</div>
              )) || <div>{lang === 'Español' ? 'Sin lesiones graves reportadas.' : 'No major injuries reported.'}</div>}

              <div className="text-rose-400 font-semibold mt-1">{getFlag(team2)} {team2}:</div>
              {injuries[cleanT2]?.map((inj: string, idx: number) => (
                <div key={idx}>• {translateInjury(inj)}</div>
              )) || <div>{lang === 'Español' ? 'Sin lesiones graves reportadas.' : 'No major injuries reported.'}</div>}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800/60">
            <h4 className="text-sm font-bold text-slate-200 mb-2 flex items-center gap-1.5">
              <Award className="w-4.5 h-4.5 text-emerald-400" />
              <span>{translateText("Last Major Standing")}</span>
            </h4>
            <div className="space-y-1.5 text-[11px] leading-relaxed">
              <div>
                <span className="text-emerald-400 font-semibold">{getFlag(team1)} {team1}:</span>{' '}
                <span className="text-slate-300">{getLastStanding(team1) || 'N/A'}</span>
              </div>
              <div>
                <span className="text-rose-400 font-semibold">{getFlag(team2)} {team2}:</span>{' '}
                <span className="text-slate-300">{getLastStanding(team2) || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Radar + Monte Carlo stacked (left) · Squad & Style comparison (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        <div className="space-y-6">
          <TeamRadarComparison
            team1={team1}
            team2={team2}
            metrics1={teamMetrics[team1]}
            metrics2={teamMetrics[team2]}
            quality={dataQuality.radar_metrics}
            lang={lang}
          />
          <MonteCarloProjections
            team1={team1}
            team2={team2}
            proj1={monteCarlo[team1]}
            proj2={monteCarlo[team2]}
            quality={dataQuality.monte_carlo_projections}
            lang={lang}
          />
        </div>
        <SquadStyleComparison
          team1={team1}
          team2={team2}
          metrics1={teamMetrics[team1]}
          metrics2={teamMetrics[team2]}
          elo1={eloRatings[team1]}
          elo2={eloRatings[team2]}
          metricQuality={dataQuality.team_metrics}
          fieldSourceCandidates={[
            metricsData.team_metric_sources,
            metricsData.squad_style_sources,
            {
              [team1]: { elo_rating: dataQuality.elo_ratings?.[team1] },
              [team2]: { elo_rating: dataQuality.elo_ratings?.[team2] },
            },
          ]}
          lang={lang}
        />
      </div>

      {/* Formation Pitch Lineup Selection */}
      <div className="glass-panel p-6">
        <h3 className="text-lg font-bold text-slate-100 mb-5 flex items-center gap-2">
          <span>{translateText("Squad Lineups")}</span>
        </h3>

        {/* Coaching & Tactical Philosophies */}
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          {translateText("Coaching & Tactical Philosophies")}
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[{ team: team1, key: cleanT1 }, { team: team2, key: cleanT2 }].map(({ team, key }) => {
            const tac = confirmed_tactics[key] || {};
            return (
              <div key={key} className="bg-slate-900/40 border border-slate-800/40 rounded-xl p-4">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-bold text-slate-100">{getFlag(team)} {team}</span>
                  <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {tac.formation || 'N/A'}
                  </span>
                </div>
                <div className="text-xs text-slate-300 font-medium mb-1">{tac.manager || '—'}</div>
                <p className="text-[11px] text-slate-400 leading-relaxed italic">{tac.philosophy || ''}</p>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <InteractivePitch
            teamName={team1}
            flag={getFlag(team1)}
            players={t1Roster}
            playerClubs={playerClubs}
            formation={confirmed_tactics[cleanT1]?.formation || "4-3-3"}
            lang={lang}
          />
          <InteractivePitch
            teamName={team2}
            flag={getFlag(team2)}
            players={t2Roster}
            playerClubs={playerClubs}
            formation={confirmed_tactics[cleanT2]?.formation || "4-3-3"}
            lang={lang}
          />
        </div>
      </div>

      {/* StatsBomb Bespoke Visualizations Section */}
      <div className="glass-panel p-6">
        <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
          <ImageIcon className="w-5 h-5 text-emerald-400" />
          <span>{lang === 'Español' ? 'Visualizaciones de Eventos del Partido (StatsBomb)' : 'Bespoke Match Event Visualizations (StatsBomb)'}</span>
        </h3>

        {/* Proxy-source disclosure: these plots use real StatsBomb data from historical proxy matches */}
        <p className="text-[11px] text-amber-400/80 font-mono mb-4 bg-amber-500/5 border border-amber-500/15 rounded-lg px-3 py-2 leading-relaxed">
          {lang === 'Español' ? 'Datos reales de StatsBomb de partidos históricos de referencia (proxy) — no hay datos de eventos del Mundial 2026 disponibles aún. ' : 'Real StatsBomb data from historical proxy matches — no World Cup 2026 event data is available yet. '}
          <span className="text-emerald-400">{getFlag(team1)} {team1}: {vizProxies[team1] || 'Proxy'}</span>
          {' · '}
          <span className="text-rose-400">{getFlag(team2)} {team2}: {vizProxies[team2] || 'Proxy'}</span>
        </p>

        {/* Tab selection */}
        <div className="flex flex-wrap gap-2 mb-6 border-b border-slate-800/60 pb-3">
          {[
            { id: 'momentum', label: lang === 'Español' ? 'Distribución de xG' : 'xG Distribution Comparison' },
            { id: 'passing', label: lang === 'Español' ? 'Red de Pases' : 'Passing Networks' },
            { id: 'shots', label: lang === 'Español' ? 'Mapa de Tiros' : 'Shot Maps' },
            { id: 'heatmaps', label: lang === 'Español' ? 'Mapa de Calor de Toques' : 'Touch Heatmaps' },
            { id: 'progressive', label: lang === 'Español' ? 'Acciones Progresivas' : 'Progressive Actions' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveVizTab(tab.id)}
              className={`px-4 py-2 text-xs font-semibold rounded-lg border transition-all duration-150 ${
                activeVizTab === tab.id
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'text-slate-400 border-transparent hover:bg-slate-900/40 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Dynamic Image display */}
        <div className="w-full flex flex-col md:flex-row gap-5 items-center justify-center p-4 bg-slate-950/20 border border-slate-800/40 rounded-2xl min-h-[300px]">
          {activeVizTab === 'momentum' && (
            <div className="w-full text-center">
              <span className="text-sm font-semibold text-slate-300 block mb-2">{getFlag(team1)} {team1} vs {getFlag(team2)} {team2}</span>
              <img 
                src={`${serverUrl}/api/visualizations/${selectedMatchId}/momentum?team=${team1}`}
                alt="xG Momentum"
                className="max-h-[360px] mx-auto rounded-xl shadow-lg border border-slate-800/50"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              <p className="text-xs text-slate-500 mt-2 font-mono">
                {lang === 'Español' ? 'Distribución de xG sin penaltis (datos proxy)' : 'Non-penalty xG distribution (proxy match data)'}
              </p>
            </div>
          )}

          {activeVizTab === 'passing' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team1)} {team1}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/passing_network?team=${team1}`}
                  alt={`${team1} Passing Network`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team2)} {team2}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/passing_network?team=${team2}`}
                  alt={`${team2} Passing Network`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
            </div>
          )}

          {activeVizTab === 'shots' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team1)} {team1}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/shot_map?team=${team1}`}
                  alt={`${team1} Shot Map`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team2)} {team2}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/shot_map?team=${team2}`}
                  alt={`${team2} Shot Map`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
            </div>
          )}

          {activeVizTab === 'heatmaps' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team1)} {team1}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/touch_heatmap?team=${team1}`}
                  alt={`${team1} Touch Heatmap`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team2)} {team2}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/touch_heatmap?team=${team2}`}
                  alt={`${team2} Touch Heatmap`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
            </div>
          )}

          {activeVizTab === 'progressive' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team1)} {team1}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/progressive_actions?team=${team1}`}
                  alt={`${team1} Progressive Actions`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
              <div className="text-center">
                <span className="text-xs font-bold text-slate-400 block mb-2">{getFlag(team2)} {team2}</span>
                <img 
                  src={`${serverUrl}/api/visualizations/${selectedMatchId}/progressive_actions?team=${team2}`}
                  alt={`${team2} Progressive Actions`}
                  className="max-h-[320px] mx-auto rounded-xl border border-slate-800/50 shadow-lg"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
