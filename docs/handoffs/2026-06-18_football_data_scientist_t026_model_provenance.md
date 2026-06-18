# Handoff - T-026 Model and Provenance Truth Review

Date: 2026-06-18  
From: Football Data Scientist  
To: Orchestrator, Data Pipeline Engineer, Frontend Engineer, QA / Reproducibility Engineer

## Summary

T-026 is complete as a read-only truth review and planning handoff. The detailed
review is documented in `docs/model_provenance.md`.

No runtime code, JSON payloads, generated data, or UI labels were changed.

## Main Findings

- The Match Analysis tab is currently driven by static `summary.json` and
  `metrics.json` files, plus runtime FastAPI augmentation.
- Dixon-Coles is currently an Elo-derived Poisson score-grid calculation, not a
  fitted or calibrated model from broad match data.
- Elo values are local hardcoded defaults, not live SoccerData or ClubElo reads.
- Seven active fixtures use the default `40/30/30` forecast fallback.
- Eight active fixtures have empty `team_metrics` objects.
- The frontend has additional silent probability/confidence fallbacks.
- "Monte Carlo Simulation Projections" is inaccurate because the current
  function is deterministic.
- StatsBomb/BigQuery charts are historical proxies, not current 2026 feeds, and
  coverage is incomplete for the project's matchday-analysis ambitions.
- Rosters, clubs, and last major standings are hardcoded frontend references.

## Wording Policy for Follow-Up Implementation

Use these truth labels until the implementation changes:

- "Elo-derived Poisson forecast with Dixon-Coles low-score adjustment"
- "local Elo default rating"
- "default forecast fallback"
- "Deterministic Elo progression estimate"
- "historical StatsBomb proxy"
- "static curated baseline preview"
- "hardcoded reference"
- "web researched" only when a source URL/path, retrieval time, and review state
  are stored.

## Handoff to Data Pipeline Engineer

Build web scraping or browser automation only under the T-035 source policy.

When source-backed intake is approved:

- collect into `briefing.json` or a documented research cache,
- preserve `summary.json` as the baseline preview,
- keep `metrics.json` source/status fields explicit,
- record URL/path, source name, retrieval time, status, and review state,
- treat missing data as `missing` or `blocked`, not invented copy.

## Handoff to Frontend Engineer

T-028 is complete and updates UI/API states so users can tell the difference between:

- model forecast,
- default forecast,
- missing forecast,
- local rating default,
- hardcoded reference,
- historical proxy,
- fresh briefing,
- stale briefing,
- baseline-only state,
- blocked source check.

## Handoff to QA / Reproducibility Engineer

Future validation should fail or warn when:

- `40/30/30` is rendered as authoritative,
- deterministic progression is labeled as Monte Carlo,
- missing team metrics render as neutral charts without disclosure,
- proxy charts fall back to unrelated teams without a source warning,
- fresh injury/lineup claims lack source metadata.

## Open User Decisions

The Orchestrator must get explicit answers before implementation:

- whether default forecasts should be shown or hidden,
- whether to rename Monte Carlo now or implement a real simulation,
- which rating source is approved,
- which web sources and scraping/browser automation rules are allowed,
- whether every AI-generated current claim requires URL-backed sources,
- whether hardcoded roster/reference data remains visible,
- and whether proxy charts should fail closed instead of using unrelated fallback
  teams.
