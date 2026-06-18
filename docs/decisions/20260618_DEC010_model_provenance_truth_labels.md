# Decision: Adopt Model and Provenance Truth Labels

Date: 2026-06-18  
Owner: Orchestrator  
Status: Accepted for documentation and follow-up implementation

## Context

T-026 found that several current labels overstate the implementation:

- Elo ratings are local defaults, not live scraped ratings.
- The forecast is an Elo-derived Poisson calculation with a Dixon-Coles
  low-score adjustment, not a fitted broad-data model.
- Some fixtures store the default `40/30/30` compatibility forecast.
- The "Monte Carlo" panel is a deterministic Elo progression curve.
- StatsBomb/BigQuery visualizations are historical proxies with incomplete
  coverage for current match analysis.
- Baseline `summary.json` content is static curated preview copy, not
  last-minute AI research.

## Decision

Adopt the truth-labeling policy documented in `docs/model_provenance.md`.

Until runtime behavior changes:

- call the forecast an "Elo-derived Poisson forecast with Dixon-Coles low-score
  adjustment",
- call current Elo inputs "local Elo default ratings",
- label `40/30/30` as a default fallback, not a model output,
- call the progression panel a "Deterministic Elo progression estimate",
- call BigQuery/StatsBomb visuals "historical proxy" visuals,
- call `summary.json` a baseline preview,
- and reserve "web researched" for facts with source metadata.

This decision did not approve a web scraping source list, browser automation,
paid provider, or automated publish workflow. T-035 now defines that source
policy.

## Consequences

- T-028 is complete and updates UI/API degraded states and misleading labels.
- T-031 must either fill or explicitly label missing metrics and rating gaps.
- T-032/T-033 must treat `briefing.json` as the source-backed matchday layer.
- Source collection must follow the T-035 allowed sources, scraping/browser
  automation rules, freshness windows, review gates, and storage policy.

## References

- `docs/model_provenance.md`
- `docs/data_contracts.md`
- `docs/last_minute_briefing_plan.md`
- `TASKS.md`
- `docs/phase_plan.md`
