# T-033 Handoff - Briefing API and Match Analysis Freshness UI

Date: 2026-06-19
Owners: Data Pipeline Engineer / Frontend Engineer
Orchestrator closeout: 2026-06-19

## Summary

T-033 is complete.

The backend now exposes a dedicated briefing route, and Match Analysis now
renders briefing freshness from that route while preserving static baseline
preview content.

## Implemented

- Added `GET /api/match/{match_id}/briefing`.
- Added shared backend helpers for:
  - summary loading
  - project-relative artifact paths
  - UTC validity parsing
  - source-label derivation
  - baseline-only fallback payloads
  - briefing artifact validation
  - summary-compatible `briefing_status`
- Updated `/api/match/{match_id}/summary` to reuse the same
  `briefing_status` derivation as the dedicated route.
- Added `BriefingFreshnessBadge`.
- Updated `MatchAnalysisTab` to fetch summary, metrics, and briefing data in
  parallel.
- Preserved summary fallback behavior when the dedicated briefing route is
  unreachable.

## API Behavior

- Missing `briefing.json`: HTTP 200, `freshness_state=baseline_only`,
  `artifact_status=missing`, `source_label=static_curated`.
- Invalid `briefing.json`: HTTP 200, `freshness_state=invalid`,
  `artifact_status=invalid`, blocked warning metadata.
- Expired `fresh` artifact: returned as `stale` based on
  `metadata.valid_until_utc`.
- Missing `summary.json`: HTTP 404 with `Summary payload not found`.

## UI Behavior

The badge supports:

- `fresh`
- `stale`
- `baseline_only`
- `blocked`
- `skipped`
- `missing`
- `invalid`

The badge shows the source label, generation age, warning/block counts, and a
reader-facing message when available. It does not replace the existing tactical
headline or static baseline preview sections.

## Verification

Commands run during closeout:

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
git diff --check
```

API smoke checks:

- `get_match_briefing("brazil_haiti_2026")` returns
  `freshness_state=baseline_only`, `artifact_status=missing`, and
  `source_label=static_curated`.
- `get_match_summary("brazil_haiti_2026")` returns the matching compact
  `briefing_status`.
- Temp-data smoke checks covered:
  - missing artifact -> `baseline_only`
  - valid fresh artifact -> `fresh`
  - expired fresh artifact -> `stale`
  - invalid artifact -> `invalid`

## Residual Risks

- No production `briefing.json` files exist yet in the repository.
- Source-backed matchday research still needs reviewed T-036 output before it
  can become production briefing content.
- Live Cloud Run is stale until a deployment task rebuilds and verifies the
  current local repo.

## Next Recommended Step

T-031 - Active Match Metrics Completion.

That task should use the T-035 source policy and T-038 source-cache pattern to
replace or explicitly preserve unavailable states for the remaining active
`team_metrics` and default-forecast gaps.
