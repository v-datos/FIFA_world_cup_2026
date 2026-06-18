# Handoff - T-027 Team Identity and Multi-Word Name Normalization

Date: 2026-06-18
From: Data Pipeline Engineer / Frontend Engineer
To: Orchestrator, Data Pipeline Engineer, Frontend Engineer, QA / Reproducibility Engineer
Status: Complete

## Deliverables

- Added canonical identity contract:
  `data/reference/team_identity.json`.
- Added Python helper:
  `src/common/team_identity.py`.
- Added React helper:
  `src/frontend/src/lib/teamIdentity.ts`.
- Updated FastAPI metrics, visualization, standings, and bracket name handling.
- Updated preview generation to use shared slugs.
- Updated React Match Analysis to resolve injury and tactics keys through the
  shared helper.
- Updated frontend flag/last-standing lookup to normalize aliases.
- Updated local bracket artifact variants for `Czech Republic`, `Turkey`, and
  `Democratic Republic of the Congo`.

## Contract for Downstream Tasks

Use these functions before writing source-backed data:

- Python:
  - `normalize_team_name(name)`
  - `canonical_team_slug(name)`
  - `team_id_to_name(team_id)`
  - `teams_from_match_id(match_id)`
- React:
  - `normalizeTeamName(team)`
  - `teamSlug(team)`
  - `getTeamIdentity(team)`

Do not create new local alias tables in T-034, T-036, T-038, or T-039. Add new
aliases to `data/reference/team_identity.json` when a source exposes a valid
provider-specific variant.

## Verification Run

- `python3 -m json.tool data/reference/team_identity.json`
- `python3 -m compileall -q src`
- Current identity audit after T-034: all 20 active fixtures resolve by folder
  ID, metadata display names, injury slugs, and tactics slugs.
- `npm --prefix src/frontend run build`

The frontend build passed with the existing chunk-size warning only.

## Next Routing

Recommended next Orchestrator task: T-028 - Incomplete Data and Fallback UI/API
States.

Reason: now that identity is stable, the public Match Analysis tab should stop
rendering default forecasts and empty Squad & Style fields as if they were
authoritative data.
