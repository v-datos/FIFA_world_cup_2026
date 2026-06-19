# DEC019 - Squad & Style Field Source Cache

Date: 2026-06-19

## Status

Accepted.

## Context

T-038 needs the Match Analysis Squad & Style panel to stop treating checked-in
team profile values as if they were source-backed matchday facts. The existing
`metrics.json.team_metrics` values mix full local profile payloads with empty
baseline stubs. Rewriting all fixture metrics from source-backed collection is
not safe until source coverage is broader and reviewed field by field.

## Decision

Adopt a separate field-level source cache for Squad & Style metrics:

- Source cache path: `data/source_cache/squad_style/latest_metrics.json`.
- Runtime reader: `src.analytics.squad_style_sources`.
- Inspector CLI: `src/pipeline/collect_squad_style_sources.py`.
- API merge point: `/api/match/{id}/metrics`.

The cache may override a runtime metric value only for the exact team and field
covered by a source record. It must not rewrite checked-in
`data/matches/{match_id}/metrics.json`.

Field-level provenance rules:

- Cached source-backed values use `source_label=web_researched`.
- Existing stored values without a source record use
  `source_label=hardcoded_reference`.
- Empty or unsupported fields use `source_label=missing`.
- Proxy values require explicit approximation metadata before they can be shown
  as approximate values.
- Historical StatsBomb/BigQuery proxy visuals must not be merged into current
  Squad & Style numeric fields.

The first T-038 sample is `brazil_haiti_2026`, because it is in the current
not-finished default workflow on 2026-06-19. Brazil has source-backed
Transfermarkt profile-header values for `squad_market_value_m` and
`average_age`. Haiti remains missing until an auditable national-team profile
source is identified.

## Consequences

- API consumers now receive `team_metric_source_cache`, `team_metric_sources`,
  and per-field `data_quality.team_metrics[team].field_sources`.
- Frontend Squad & Style rows can show sourced, reference, approximate, missing,
  unsupported, or blocked states per displayed value.
- T-031 remains responsible for broad source coverage across teams and fields.
- T-038 is complete as a contract and partial source-backed integration; it is
  not a claim that every Squad & Style metric now has live source coverage.

## Verification

- `python3 src/pipeline/collect_squad_style_sources.py`
- `python3 -m json.tool data/source_cache/squad_style/latest_metrics.json`
- Direct API smoke checks for `brazil_haiti_2026` and a non-sample fixture
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
