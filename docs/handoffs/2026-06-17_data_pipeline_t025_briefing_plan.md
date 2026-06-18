# Handoff - T-025 Safe Last-Minute Match Briefing Generation Plan

Date: 2026-06-17  
From: Data Pipeline Engineer  
To: Orchestrator, Football Data Scientist, Frontend Engineer, QA / Reproducibility Engineer

## Summary

T-025 is complete as a planning task. The plan is documented in
`docs/last_minute_briefing_plan.md`.

The central decision is to keep long-lived baseline previews separate from
matchday briefings:

- Baseline preview: `data/matches/{match_id}/summary.json`
- Last-minute briefing: planned `data/matches/{match_id}/briefing.json`

No runtime code or JSON data was changed.

## Implementation Guardrails

- Do not overwrite `summary.json` or `metrics.json` when generating briefings.
- Build a separate `generate_match_briefings.py` flow.
- Default to dry-run.
- Require explicit write mode.
- Read fixture/team names from `summary.json`, not from match ID splitting.
- Generate only active-date or next-24-hour briefings by default.
- Surface empty metrics, default forecasts, source failures, and missing review
  as validation warnings or blocked reasons.

## Routed Follow-Ups

- T-026: model/provenance wording before approved briefing output.
- T-027: team identity normalization before implementation depends on team keys.
- T-028: incomplete/fallback/freshness states.
- T-032: briefing pipeline implementation.
- T-033: briefing API and Match Analysis UI integration.

## Verification Expected Later

- Dry-run writes nothing.
- Write mode creates or updates only `briefing.json`.
- `summary.json` and `metrics.json` remain unchanged.
- Fresh, stale, baseline-only, and blocked states are testable.
- Python compile and frontend build pass.

