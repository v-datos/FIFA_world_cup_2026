# T-038 Handoff - Source-Backed Squad & Style Metrics Integration

Date: 2026-06-19
Owners: Data Pipeline Engineer / Football Data Scientist / Frontend Engineer
Orchestrator closeout: 2026-06-19

## Summary

T-038 is complete for the first conservative Squad & Style source-backed
integration pass.

The task added a field-level source cache and runtime merge path so the API/UI
can distinguish source-backed values from local reference values and missing
fields. Checked-in `metrics.json` payloads are not rewritten.

## Implemented

- Added `docs/squad_style_source_methodology.md`.
- Added `data/source_cache/squad_style/latest_metrics.json`.
- Added `src/analytics/squad_style_sources.py`.
- Added `src/pipeline/collect_squad_style_sources.py`.
- Updated `/api/match/{id}/metrics` to expose:
  - `team_metric_source_cache`
  - `team_metric_sources`
  - `data_quality.team_metrics[team].fields`
  - `data_quality.team_metrics[team].field_sources`
- Updated Squad & Style frontend rendering with compact per-value provenance
  badges and source tooltips.
- Renamed the rating row to World Football Elo and wired T-039 Elo provenance
  into the Squad & Style row.

## Sample Fixture

The initial sample is `brazil_haiti_2026`, because it is in the current
not-finished workflow on 2026-06-19.

Source-backed fields:

| Team | Field | Value | Source |
|---|---:|---:|---|
| Brazil | `squad_market_value_m` | `928.2` | Transfermarkt Brazil profile header |
| Brazil | `average_age` | `29.4` | Transfermarkt Brazil profile header |

Haiti remains explicit `missing` for Squad & Style fields because no auditable
national-team Transfermarkt profile was identified during this pass.

## Provenance Rules

- Source-backed cache fields: `web_researched`.
- Existing stored values without field source records: `hardcoded_reference`.
- No value or unsupported source coverage: `missing`.
- Proxy values are not allowed unless future records include approximation
  metadata.
- Historical StatsBomb/BigQuery proxy data remains visual context only.

## Verification

Commands run during closeout:

```bash
python3 src/pipeline/collect_squad_style_sources.py
python3 -m json.tool data/source_cache/squad_style/latest_metrics.json
python3 -m compileall -q src
npm --prefix src/frontend run build
```

API smoke checks:

- `get_match_metrics("brazil_haiti_2026")` returns source-backed Brazil
  `squad_market_value_m` and `average_age`, missing Haiti fields, and
  `teams_with_manifest_rows=["Brazil", "Haiti"]`.
- `get_match_metrics("france_senegal_2026")` keeps existing full local profile
  values labeled `hardcoded_reference` because there are no T-038 source
  records for that finished fixture.

## Residual Risks

- Transfermarkt values are source-backed reference estimates, not official FIFA
  squad valuations.
- Haiti source coverage is still missing.
- Broad coverage for all fixtures and all 15 `team_metrics` fields remains
  T-031 work.
- True PPDA and true field tilt still require event/spatial source coverage or
  explicit proxy methodology.
