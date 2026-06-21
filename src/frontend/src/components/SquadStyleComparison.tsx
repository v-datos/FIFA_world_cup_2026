import React from 'react';
import { getFlag } from '../lib/teamData';
import { translateTeamName, translateSourceLabel } from '../lib/translations';

type MetricValue = number | string | null | undefined;
type MetricRecord = Record<string, MetricValue>;
type SourceRecord = {
  status?: string;
  state?: string;
  source_status?: string;
  source_label?: string;
  source_name?: string;
  source?: string;
  label?: string;
  provenance?: string;
  provenance_label?: string;
  message?: string;
  note?: string;
  url?: string;
  source_url?: string;
  retrieved_at?: string;
  reviewed_at?: string;
  updated_at?: string;
  checked_at_utc?: string;
  retrieval_method?: string;
  approximation?: boolean;
  approximation_note?: string;
};
type TeamMetricQuality = SourceRecord & {
  missing_fields?: unknown;
  field_sources?: Record<string, unknown>;
};

interface Props {
  team1: string;
  team2: string;
  metrics1?: MetricRecord;
  metrics2?: MetricRecord;
  elo1?: number | null;
  elo2?: number | null;
  metricQuality?: Record<string, TeamMetricQuality>;
  fieldSourceCandidates?: Array<Record<string, unknown> | undefined>;
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
  sourceKeys?: string[];
};

type FieldState = SourceRecord & {
  unavailable?: boolean;
  approximate?: boolean;
};

const isRecord = (value: unknown): value is Record<string, unknown> => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
);

const cleanText = (value: unknown): string | undefined => (
  typeof value === 'string' && value.trim() ? value.trim() : undefined
);

const sourceFromUnknown = (value: unknown): SourceRecord | undefined => {
  if (typeof value === 'string') {
    return { source_label: value };
  }
  if (!isRecord(value)) return undefined;

  const source: SourceRecord = {
    status: cleanText(value.status),
    state: cleanText(value.state),
    source_status: cleanText(value.source_status),
    source_label: cleanText(value.source_label),
    source_name: cleanText(value.source_name),
    source: cleanText(value.source),
    label: cleanText(value.label),
    provenance: cleanText(value.provenance),
    provenance_label: cleanText(value.provenance_label),
    message: cleanText(value.message),
    note: cleanText(value.note),
    url: cleanText(value.url),
    source_url: cleanText(value.source_url),
    retrieved_at: cleanText(value.retrieved_at),
    reviewed_at: cleanText(value.reviewed_at),
    updated_at: cleanText(value.updated_at),
    checked_at_utc: cleanText(value.checked_at_utc),
    retrieval_method: cleanText(value.retrieval_method),
    approximation: typeof value.approximation === 'boolean' ? value.approximation : undefined,
    approximation_note: cleanText(value.approximation_note),
  };

  return Object.values(source).some(Boolean) ? source : undefined;
};

const sourceWords = (source?: SourceRecord): string => (
  [
    source?.status,
    source?.state,
    source?.source_status,
    source?.source_label,
    source?.source,
    source?.label,
    source?.provenance,
    source?.provenance_label,
  ].filter(Boolean).join(' ').toLowerCase()
);

const fieldMarkedMissing = (quality: TeamMetricQuality | undefined, fieldKeys: string[]): boolean => {
  const missing = quality?.missing_fields;
  if (Array.isArray(missing)) {
    return fieldKeys.some((field) => missing.includes(field));
  }
  if (!isRecord(missing)) return false;

  return fieldKeys.some((field) => {
    const marker = missing[field];
    if (typeof marker === 'boolean') return marker;
    if (typeof marker === 'string') return ['missing', 'unavailable', 'unsupported'].includes(marker.toLowerCase());
    return false;
  });
};

const findFieldSource = (
  sourceMap: Record<string, unknown> | undefined,
  team: string,
  fieldKeys: string[],
): SourceRecord | undefined => {
  if (!sourceMap) return undefined;

  const teamRecord = sourceMap[team];
  if (isRecord(teamRecord)) {
    for (const field of fieldKeys) {
      const source = sourceFromUnknown(teamRecord[field]);
      if (source) return source;
    }
  }

  for (const field of fieldKeys) {
    const fieldRecord = sourceMap[field];
    if (isRecord(fieldRecord)) {
      const source = sourceFromUnknown(fieldRecord[team]);
      if (source) return source;
    }

    const directSource = sourceFromUnknown(fieldRecord);
    if (directSource) return directSource;

    const dottedSource = sourceFromUnknown(sourceMap[`${team}.${field}`]);
    if (dottedSource) return dottedSource;
  }

  return undefined;
};

export const SquadStyleComparison: React.FC<Props> = ({
  team1,
  team2,
  metrics1 = {},
  metrics2 = {},
  elo1,
  elo2,
  metricQuality = {},
  fieldSourceCandidates = [],
  lang,
}) => {
  const es = lang === 'Español';
  const q1 = metricQuality[team1];
  const q2 = metricQuality[team2];
  const bothMissing = q1?.status === 'missing' && q2?.status === 'missing';
  const anyMissing = q1?.status === 'missing' || q2?.status === 'missing' || q1?.status === 'partial' || q2?.status === 'partial';
  const rawSourceLabel = q1?.source_label || q2?.source_label || 'static_curated';
  const sourceLabel = bothMissing
    ? (es ? 'Métricas no disponibles' : 'Metrics unavailable')
    : (translateSourceLabel(rawSourceLabel, lang) || rawSourceLabel.replace(/_/g, ' '));

  const rows: Row[] = [
    { label: es ? 'Posesión Media' : 'Average Possession', key: 'possession_avg', suffix: '%', dec: 1 },
    { label: es ? 'Valor de Plantilla' : 'Squad Market Value', key: 'squad_market_value_m', prefix: '€', suffix: 'M', dec: 1 },
    { label: es ? 'Edad Media' : 'Average Age', key: 'average_age', suffix: ' yrs', dec: 1, neutral: true },
    { label: es ? 'World Football Elo' : 'World Football Elo Rating', elo: true, dec: 0, sourceKeys: ['world_football_elo', 'elo_rating', 'club_elo_rating', 'club_elo'] },
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
  ];

  const toNumber = (value: MetricValue): number => {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') return Number.parseFloat(value);
    return Number.NaN;
  };

  const num = (row: Row, m: MetricRecord, elo?: number | null): number | null => {
    if (row.elo) return elo ?? null;
    const v = toNumber(m[row.key as string]);
    return isNaN(v) ? null : v;
  };

  const fmt = (row: Row, v: number | null): string => {
    if (v === null) return '—';
    return `${row.prefix ?? ''}${v.toFixed(row.dec)}${row.suffix ?? ''}`;
  };

  const rowSourceKeys = (row: Row): string[] => (
    row.sourceKeys || (row.key ? [row.key] : [])
  );

  const resolveFieldState = (team: string, row: Row, value: number | null): FieldState => {
    const fieldKeys = rowSourceKeys(row);
    const quality = metricQuality[team];
    const fieldSource = fieldKeys
      .map((field) => sourceFromUnknown(quality?.field_sources?.[field]))
      .find((source): source is SourceRecord => Boolean(source));
    const candidateSource = fieldSourceCandidates
      .map((candidate) => findFieldSource(candidate, team, fieldKeys))
      .find((source): source is SourceRecord => Boolean(source));
    const source = fieldSource || candidateSource;
    const words = sourceWords(source);
    const qualityWords = sourceWords(quality);
    const unavailable = (
      value === null ||
      fieldMarkedMissing(quality, fieldKeys) ||
      /missing|unavailable|unsupported|blocked/.test(words) ||
      /missing|unavailable|unsupported|blocked/.test(qualityWords)
    );

    if (unavailable) {
      return {
        ...(source || quality || {}),
        status: source?.status || quality?.status || 'missing',
        source_label: source?.source_label || quality?.source_label || 'missing',
        message: source?.message || quality?.message || (es
          ? 'Este campo no tiene una métrica disponible para este equipo.'
          : 'This field has no available metric for this team.'),
        unavailable: true,
      };
    }

    if (source) return source;

    if (row.elo) {
      return {
        status: 'reference',
        source_label: 'hardcoded_reference',
        message: es
          ? 'Valor local de referencia Elo; no es una fuente en vivo.'
          : 'Local Elo reference value; not a live source feed.',
        approximate: true,
      };
    }

    if (quality?.status || quality?.source_label || quality?.message) {
      return {
        status: quality.status,
        source_label: quality.source_label,
        message: quality.message || (es
          ? 'Sin fuente de campo específica; se muestra con la calidad general del equipo.'
          : 'No field-specific source; shown with the team-level quality state.'),
        approximate: true,
      };
    }

    return {
      status: 'approximate',
      source_label: 'approximate',
      message: es
        ? 'Sin metadatos de fuente a nivel de campo todavía.'
        : 'No field-level source metadata is available yet.',
      approximate: true,
    };
  };

  const fieldStateKind = (source: FieldState): 'missing' | 'unsupported' | 'blocked' | 'approximate' | 'sourced' | 'reference' => {
    const words = sourceWords(source);
    if (/unsupported/.test(words)) return 'unsupported';
    if (/blocked/.test(words)) return 'blocked';
    if (source.unavailable || /missing|unavailable/.test(words)) return 'missing';
    if (/hardcoded_reference|reference/.test(words)) return 'reference';
    if (source.approximate || source.approximation || /default_forecast|proxy_historical|static_curated|approx|estimate|fallback|curated|partial/.test(words)) return 'approximate';
    return 'sourced';
  };

  const badgeText = (source: FieldState): string => {
    const kind = fieldStateKind(source);
    if (kind === 'unsupported') return es ? 'sin dato' : 'unsupported';
    if (kind === 'blocked') return es ? 'bloq.' : 'blocked';
    if (kind === 'missing') return es ? 'faltante' : 'missing';
    if (kind === 'reference') return 'ref';
    if (kind === 'approximate') return es ? 'aprox.' : 'approx';

    const label = source.source_label || source.source || source.label || source.provenance_label;
    if (!label) return es ? 'fuente' : 'sourced';
    return label.replace(/_/g, ' ').slice(0, 14);
  };

  const badgeClass = (source: FieldState): string => {
    const kind = fieldStateKind(source);
    if (kind === 'sourced') return 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300';
    if (kind === 'missing' || kind === 'unsupported' || kind === 'blocked') {
      return 'border-amber-500/25 bg-amber-500/10 text-amber-200';
    }
    return 'border-slate-600/40 bg-slate-800/45 text-slate-300';
  };

  const sourceTitle = (team: string, row: Row, source: FieldState): string => (
    [
      `${team} · ${row.label}`,
      `State: ${source.status || source.state || source.source_label || 'source'}`,
      source.source_label && `Source: ${source.source_label.replace(/_/g, ' ')}`,
      source.source_name && `Source name: ${source.source_name}`,
      source.message || source.note,
      source.approximation_note && `Approximation: ${source.approximation_note}`,
      source.source_url || source.url,
      source.checked_at_utc && `Checked: ${source.checked_at_utc}`,
      source.retrieval_method && `Method: ${source.retrieval_method}`,
      source.retrieved_at && `Retrieved: ${source.retrieved_at}`,
      source.reviewed_at && `Reviewed: ${source.reviewed_at}`,
      source.updated_at && `Updated: ${source.updated_at}`,
    ].filter(Boolean).join('\n')
  );

  const renderValue = (
    team: string,
    row: Row,
    value: number | null,
    better: boolean,
    align: 'left' | 'right',
  ) => {
    const fieldState = resolveFieldState(team, row, value);
    const displayValue = fieldState.unavailable ? '—' : fmt(row, value);
    const color = better
      ? (align === 'left' ? 'text-emerald-400' : 'text-rose-400')
      : (fieldState.unavailable ? 'text-slate-500' : 'text-slate-300');

    return (
      <span className={`min-w-0 flex items-center gap-1.5 ${align === 'right' ? 'justify-end text-right' : 'justify-start text-left'}`}>
        <span className={`font-mono text-sm font-bold ${color}`}>{displayValue}</span>
        <span
          className={`shrink-0 max-w-20 truncate rounded border px-1 py-0.5 text-[8px] font-bold uppercase tracking-wide ${badgeClass(fieldState)}`}
          title={sourceTitle(team, row, fieldState)}
        >
          {badgeText(fieldState)}
        </span>
      </span>
    );
  };

  return (
    <div className="w-full h-full glass-panel p-5 flex flex-col">
      <h3 className="text-lg font-bold text-slate-100">
        {es ? 'Comparación de Plantilla y Estilo' : 'Squad & Style Comparison'}
      </h3>
      <p className="text-xs text-slate-400">{sourceLabel}</p>

      <div className="flex justify-between items-center text-sm font-bold mt-4 mb-2 pb-2 border-b border-slate-800/60">
        <span className="text-emerald-400">{getFlag(team1)} {translateTeamName(team1, lang)}</span>
        <span className="text-rose-400">{translateTeamName(team2, lang)} {getFlag(team2)}</span>
      </div>

      {anyMissing && !bothMissing && (
        <div className="mb-3 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100/75 leading-relaxed">
          {es
            ? 'Algunas métricas no están disponibles; los campos faltantes se muestran como —.'
            : 'Some metrics are unavailable; missing fields are shown as —.'}
        </div>
      )}

      <div className="flex-1 flex flex-col justify-between mt-1">
        {bothMissing ? (
          <div className="flex-1 rounded-xl border border-amber-500/25 bg-amber-500/10 p-4 flex flex-col items-center justify-center text-center">
            <div className="text-sm font-bold text-amber-300">
              {es ? 'Comparación no disponible' : 'Comparison unavailable'}
            </div>
            <p className="text-xs text-amber-100/75 mt-2 leading-relaxed">
              {q1?.message || q2?.message || (es
                ? 'No hay métricas de plantilla o estilo para este partido.'
                : 'No squad or style metrics are available for this fixture.')}
            </p>
          </div>
        ) : rows.map((row) => {
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
              {renderValue(team1, row, n1, better === 1, 'left')}
              <span className="text-[10px] text-slate-500 text-center uppercase tracking-wide px-1">
                {row.label}
              </span>
              {renderValue(team2, row, n2, better === 2, 'right')}
            </div>
          );
        })}
      </div>
    </div>
  );
};
