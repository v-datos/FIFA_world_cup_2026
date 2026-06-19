# DEC021 - Briefing API Freshness Contract

Date: 2026-06-19

## Status

Accepted.

## Context

T-032 created safe `briefing.json` generation, but Match Analysis still needed a
dedicated API/UI contract for freshness states. The app must not imply fresh
last-minute analysis when no briefing artifact exists, and it must not hide the
static curated preview content when matchday research is missing, stale,
blocked, skipped, or invalid.

## Decision

Adopt `GET /api/match/{match_id}/briefing` as the full briefing consumption
route.

The route must:

- Load valid `data/matches/{match_id}/briefing.json` artifacts when present.
- Return HTTP 200 with a `baseline_only` fallback when `briefing.json` is
  missing.
- Return HTTP 200 with an `invalid` fallback when the artifact cannot be read or
  fails required-block validation.
- Downgrade `fresh` artifacts to `stale` at response time when
  `metadata.valid_until_utc` has expired.
- Return a compact `briefing_status` block that `/api/match/{match_id}/summary`
  can reuse for compatibility.

Match Analysis must fetch the dedicated briefing route, fall back to
`summary.briefing_status` when needed, and render freshness as status metadata
without replacing or suppressing the static tactical preview.

## Consequences

- Missing briefing artifacts are visible as `baseline_only`, not as broken
  analysis.
- Invalid artifacts are blocked from being treated as available.
- UI consumers can show fresh, stale, baseline-only, blocked, skipped, missing,
  and invalid states consistently.
- T-031 can now focus on remaining active metric coverage rather than briefing
  API plumbing.
- Source-backed research still requires the T-036/T-035 review flow before it is
  merged into production briefing artifacts.

## Verification

- Direct API smoke check for `brazil_haiti_2026` briefing fallback.
- Direct API smoke check for matching summary `briefing_status`.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
- `git diff --check`
