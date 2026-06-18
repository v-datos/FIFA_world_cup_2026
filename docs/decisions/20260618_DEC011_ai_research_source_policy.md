# Decision: Approve AI Research Source Policy

Date: 2026-06-18  
Owner: Orchestrator  
Status: Accepted

## Context

The user clarified the desired project direction after T-026:

- default forecasts should render as unavailable,
- the progression panel should become a real Monte Carlo simulation,
- source-backed online research should replace hardcoded data where practical,
- browser automation and scraping are allowed,
- not every displayed AI claim needs a direct URL citation,
- and last-minute freshness should use a 3-hour window before the first game of
  the matchday `jornada`.

## Decision

Adopt `docs/ai_research_source_policy.md` as the source policy and data intake
architecture for T-035.

The recommended source stack is:

- World Football Elo as the primary rating source, with FIFA ranking as fallback
  or sanity check.
- FIFA official sources for squads, ranking, and tournament facts.
- Sportmonks as the preferred structured provider for lineups, injuries, squads,
  formations, xG/statistics where plan coverage allows.
- API-Football as a structured fallback provider.
- Transfermarkt for squad and market-value data.
- Wyscout, Opta/Stats Perform, or paid StatsBomb/event feeds for reliable PPDA,
  field tilt, and event-style metrics when budget/access allows.
- Browser automation over official/team/news sources for last-minute tactical
  and injury updates.

## Consequences

- T-035 is complete as a policy/planning task.
- T-028 should show "forecast unavailable" for default forecasts.
- T-037 should replace the deterministic progression formula with a real Monte
  Carlo simulation.
- T-036 should prototype source-backed research collection for one fixture.
- T-038 should integrate source-backed Squad & Style metrics.
- Browser automation is allowed, but source snapshots and collection metadata
  must still be retained for operator audit.

## References

- `docs/ai_research_source_policy.md`
- `docs/model_provenance.md`
- `docs/data_contracts.md`
- `TASKS.md`
- `docs/phase_plan.md`
