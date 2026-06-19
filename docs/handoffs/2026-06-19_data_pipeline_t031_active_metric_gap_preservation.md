# T-031 Active Match Metrics Completion Handoff

Date: 2026-06-19

From: Data Pipeline Engineer / Football Data Scientist

To: Orchestrator

## Summary

T-031 is complete as an unavailable-state preservation pass. The remaining
active empty Squad & Style metric gaps were not filled with invented values.
Instead, the T-038 source-cache manifest now carries explicit missing rows for
the affected active teams, and the API exposes those row-level missing reasons
in data-quality metadata.

The Football Data Scientist ownership decision is that explicit `missing` is
the correct football-methodology outcome when no approved source-cache record
exists under T-035. These fields should be replaced only by reviewed
field-level source records, not by local profile defaults, historical proxies,
or AI inference.

## Files Changed

- `src/analytics/squad_style_sources.py`
- `src/api/main.py`
- `data/source_cache/squad_style/latest_metrics.json`
- `TASKS.md`
- `STATUS.md`
- `docs/phase_plan.md`
- `docs/data_contracts.md`
- `docs/decisions/20260619_DEC022_active_metric_gap_preservation.md`
- `docs/handoffs/2026-06-19_data_pipeline_t031_active_metric_gap_preservation.md`

## Behavior

- Source-backed Squad & Style values still merge only from
  `data/source_cache/squad_style/latest_metrics.json`.
- The cache now includes explicit `missing` rows for active teams with empty
  `team_metrics` and no approved local source-cache record.
- `/api/match/{id}/metrics.data_quality.team_metrics[*]` missing records now
  include `source_cache_status`, `missing_reasons`, and `blocked_reasons`.
- `data/matches/**/metrics.json` was not rewritten.
- Default 40/30/30 forecasts remain `default_forecast`.

## Verification

- `python3 src/pipeline/collect_squad_style_sources.py`
  - Returned `team_count=18`, `field_record_count=2`, `status=partial`.
- `python3 -m json.tool data/source_cache/squad_style/latest_metrics.json`
  - Passed.
- Direct API smoke with `simulation_count=10000`, `seed=20260619`:
  - `canada_qatar_2026`: default forecast unavailable; both teams missing with
    `no_approved_local_squad_style_source_cache`.
  - `brazil_haiti_2026`: default forecast unavailable; Brazil partial with two
    source-backed fields; Haiti missing.
  - `switzerland_bosnia_and_herzegovina_2026`: non-default stored forecast
    available; both team metric profiles missing.
  - `argentina_algeria_2026`: full local profiles remain
    `hardcoded_reference`.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
  - Passed with the existing Vite chunk-size warning.
- `git diff --check`

## Residual Risks

- No new public-source collector was implemented. Future source-backed field
  completion still requires reviewed source records or a collector that follows
  T-035.
- Most Squad & Style fields remain unavailable for the active empty fixtures.
- API smoke imports still emit Streamlit cache warnings in local script mode;
  they did not block response validation.

## Next Routing

Route next work to T-030 Streamlit Legacy Disposition unless the Orchestrator
prioritizes a reviewed Squad & Style collector for a specific source family.
