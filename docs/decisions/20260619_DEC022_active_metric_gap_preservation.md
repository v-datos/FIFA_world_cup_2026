# DEC022 - Active Metric Gap Preservation

Date: 2026-06-19

## Status

Accepted.

## Context

T-031 followed T-038's field-level Squad & Style source-cache pattern. The
remaining active fixtures with empty `team_metrics` had no approved local
source-cache records for current squad/style values. Under the T-035 source
policy, those values cannot be inferred from default forecasts, historical
proxies, local profile defaults, or unsupported web assumptions.

## Decision

Preserve unavailable active metric gaps as explicit source-cache rows:

- Keep source-backed Squad & Style values in
  `data/source_cache/squad_style/latest_metrics.json`.
- Do not rewrite curated `data/matches/**/metrics.json` fixture payloads for
  unavailable values.
- Add manifest rows with `status=missing`, `source_label=missing`, and
  machine-readable `missing_reasons` when no approved local source-cache record
  exists for an active empty team profile.
- Carry row-level manifest metadata through
  `/api/match/{id}/metrics.data_quality.team_metrics[*]` and per-field
  `field_sources`.
- Continue labeling default 40/30/30 forecasts as `default_forecast`, not as
  model probabilities.

## Consequences

- API consumers can distinguish explicit T-031 unavailable states from a missing
  or unreadable cache.
- The only current source-backed Squad & Style fields remain Brazil
  `squad_market_value_m` and `average_age` for `brazil_haiti_2026`.
- Future collectors can replace a missing row field-by-field by adding audited
  source records to the cache.
- Unsupported fields stay `missing`; they are not backfilled from
  `hardcoded_reference`, `proxy_historical`, or AI-inferred values.

## Verification

- `python3 src/pipeline/collect_squad_style_sources.py`
- `python3 -m json.tool data/source_cache/squad_style/latest_metrics.json`
- Direct API smoke for `canada_qatar_2026`, `brazil_haiti_2026`,
  `switzerland_bosnia_and_herzegovina_2026`, and `argentina_algeria_2026`
- `python3 -m compileall -q src`
- `git diff --check`
