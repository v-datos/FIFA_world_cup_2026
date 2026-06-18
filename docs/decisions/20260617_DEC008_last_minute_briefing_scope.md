# Decision: Separate Baseline Previews from Last-Minute Match Briefings

Date: 2026-06-17  
Owner: Orchestrator  
Status: Accepted

## Context

The project currently has 19 active `data/matches/*_2026` folders. That count
is an artifact of static generated folders and the existing generator behavior,
not a product rule.

The existing `summary.json` files are useful baseline tactical previews, but
they may be created days or weeks before kickoff. Presenting that content as
last-minute AI analysis would misrepresent its freshness.

The current preview generator also has overwrite risk: it can write
`summary.json` and `metrics.json` directly. That is not acceptable for
matchday briefing updates.

## Decision

T-025 is re-scoped from "Safe Preview Generation Plan" to "Safe Last-Minute
Match Briefing Generation Plan".

The project will separate:

- Baseline previews in `summary.json`.
- Matchday updates in a planned `briefing.json`.

The planned briefing pipeline must:

- Generate only `data/matches/{match_id}/briefing.json`.
- Default to dry-run.
- Require explicit write mode.
- Preserve `summary.json` and `metrics.json`.
- Include freshness, source, validation, and review metadata.
- Support active-date or next-24-hour generation windows instead of generating
  all future static folders by default.

## Consequences

- T-025 is completed as a planning/specification task.
- Implementation moves to T-032: Last-Minute Briefing Pipeline Implementation.
- API/UI consumption moves to T-033 and should coordinate with T-028.
- T-026 should review model/provenance wording before briefings are approved.
- T-027 should resolve team identity normalization before relying on generated
  team keys across pipeline/API/UI.

## References

- `docs/last_minute_briefing_plan.md`
- `docs/data_contracts.md`
- `TASKS.md`
- `docs/phase_plan.md`

