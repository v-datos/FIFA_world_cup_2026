import React from 'react';
import { AlertTriangle, CheckCircle2, Clock, FileClock } from 'lucide-react';
import { translateSourceLabel, translateBriefingMessage } from '../lib/translations';

export type BriefingFreshnessStatus = {
  freshness_state?: string;
  source_label?: string;
  message?: string;
  generated_at_utc?: string;
  valid_until_utc?: string;
  checked_at_utc?: string;
  status_origin?: string;
  source_count?: number;
  warnings?: string[];
  blocked_reasons?: string[];
};

interface Props {
  status?: BriefingFreshnessStatus | null;
  lang: string;
}

const cleanState = (state?: string): string => (
  (state || 'missing').trim().toLowerCase()
);

const stateLabel = (state: string, es: boolean): string => {
  const labels: Record<string, { en: string; es: string }> = {
    fresh: { en: 'Last-minute fresh', es: 'Ultimo minuto vigente' },
    stale: { en: 'Briefing stale', es: 'Briefing vencido' },
    baseline_only: { en: 'Baseline preview', es: 'Vista base' },
    blocked: { en: 'Briefing blocked', es: 'Briefing bloqueado' },
    skipped: { en: 'Briefing skipped', es: 'Briefing omitido' },
    missing: { en: 'Briefing missing', es: 'Briefing faltante' },
    invalid: { en: 'Briefing invalid', es: 'Briefing invalido' },
  };
  const label = labels[state] || { en: state.replace(/_/g, ' '), es: state.replace(/_/g, ' ') };
  return es ? label.es : label.en;
};

const sourceLabel = (label: string | undefined, es: boolean): string | undefined => {
  if (!label) return undefined;
  return translateSourceLabel(label, es ? 'Español' : 'English');
};

const parseDate = (value?: string): Date | null => {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};

const shortDateTime = (value: string | undefined, es: boolean): string | undefined => {
  const date = parseDate(value);
  if (!date) return undefined;
  return new Intl.DateTimeFormat(es ? 'es' : 'en', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

const ageText = (value: string | undefined, es: boolean): string | undefined => {
  const date = parseDate(value);
  if (!date) return undefined;

  const diffMs = Date.now() - date.getTime();
  const absMinutes = Math.max(0, Math.round(Math.abs(diffMs) / 60000));
  const suffix = diffMs >= 0 ? (es ? 'hace' : 'ago') : (es ? 'en' : 'in');

  if (absMinutes < 90) {
    return es
      ? `${suffix} ${absMinutes}m`
      : `${absMinutes}m ${suffix}`;
  }

  const hours = Math.round(absMinutes / 60);
  if (hours < 48) {
    return es
      ? `${suffix} ${hours}h`
      : `${hours}h ${suffix}`;
  }

  const days = Math.round(hours / 24);
  return es
    ? `${suffix} ${days}d`
    : `${days}d ${suffix}`;
};

const stateClasses = (state: string): string => {
  if (state === 'fresh') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
  if (state === 'blocked' || state === 'invalid') return 'border-rose-500/30 bg-rose-500/10 text-rose-200';
  if (state === 'stale' || state === 'missing') return 'border-amber-500/30 bg-amber-500/10 text-amber-200';
  return 'border-slate-700/70 bg-slate-950/35 text-slate-300';
};

const StatusIcon = ({ state }: { state: string }) => {
  if (state === 'fresh') return <CheckCircle2 className="h-3.5 w-3.5" />;
  if (state === 'blocked' || state === 'invalid') return <AlertTriangle className="h-3.5 w-3.5" />;
  if (state === 'stale') return <Clock className="h-3.5 w-3.5" />;
  return <FileClock className="h-3.5 w-3.5" />;
};

export const BriefingFreshnessBadge: React.FC<Props> = ({ status, lang }) => {
  const es = lang === 'Español';
  const state = cleanState(status?.freshness_state);
  const source = sourceLabel(status?.source_label, es);
  const generatedText = ageText(status?.generated_at_utc, es);
  const checkedText = shortDateTime(status?.checked_at_utc || status?.generated_at_utc, es);
  const warningCount = status?.warnings?.length || 0;
  const blockedCount = status?.blocked_reasons?.length || 0;
  const detailParts = [
    translateBriefingMessage(status?.message, lang),
    source && `${es ? 'Fuente' : 'Source'}: ${source}`,
    generatedText && `${es ? 'Generado' : 'Generated'}: ${generatedText}`,
    checkedText && `${es ? 'Revisado' : 'Checked'}: ${checkedText}`,
    status?.valid_until_utc && `${es ? 'Valido hasta' : 'Valid until'}: ${shortDateTime(status.valid_until_utc, es)}`,
    typeof status?.source_count === 'number' && `${es ? 'Fuentes' : 'Sources'}: ${status.source_count}`,
    warningCount > 0 && `${es ? 'Avisos' : 'Warnings'}: ${warningCount}`,
    blockedCount > 0 && `${es ? 'Bloqueos' : 'Blocks'}: ${blockedCount}`,
    status?.status_origin && `${es ? 'Origen' : 'Origin'}: ${status.status_origin}`,
  ].filter(Boolean).join('\n');

  if (state === 'baseline_only' || state === 'missing') {
    return null;
  }

  return (
    <div
      className={`mt-3 inline-flex max-w-full flex-wrap items-center gap-2 rounded-lg border px-3 py-2 text-[10px] font-mono ${stateClasses(state)}`}
      title={detailParts || stateLabel(state, es)}
    >
      <span className="inline-flex items-center gap-1.5 font-bold uppercase tracking-wide">
        <StatusIcon state={state} />
        <span>{stateLabel(state, es)}</span>
      </span>
      {source && (
        <span className="rounded border border-current/20 px-1.5 py-0.5 uppercase tracking-wide opacity-90">
          {source}
        </span>
      )}
      {generatedText && (
        <span className="text-slate-300/80 normal-case tracking-normal">
          {generatedText}
        </span>
      )}
      {(warningCount > 0 || blockedCount > 0) && (
        <span className="text-slate-300/80 normal-case tracking-normal">
          {warningCount + blockedCount} {es ? 'alertas' : 'alerts'}
        </span>
      )}
      {status?.message && (
        <span className="max-w-full truncate text-slate-300/80 normal-case tracking-normal sm:max-w-md">
          {translateBriefingMessage(status.message, lang)}
        </span>
      )}
    </div>
  );
};
