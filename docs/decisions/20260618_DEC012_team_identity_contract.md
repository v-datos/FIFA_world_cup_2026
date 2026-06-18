# DEC012 - Adopt Shared Team Identity Contract

Date: 2026-06-18
Status: Accepted
Task: T-027 - Team Identity and Multi-Word Name Normalization

## Context

The app previously derived team names and slugs in several places:

- FastAPI standings, metrics, and visualization routes.
- `generate_match_previews.py`.
- React Match Analysis editorial lookups.
- Frontend flag and roster fallbacks.
- Legacy Streamlit bracket helpers.

That duplication caused known failures for multi-word teams, especially
`democratic_republic_of_the_congo` and `bosnia_and_herzegovina`, and would make
source-backed collectors risky because providers use variants such as `DR Congo`,
`Czechia`, `Turkiye`, `Türkiye`, `Curaçao`, and `Côte d'Ivoire`.

## Decision

Use `data/reference/team_identity.json` as the canonical team identity contract.

The contract contains:

- API `team_id`
- canonical project display name
- canonical JSON/UI slug
- flag
- accepted aliases

Python code must use `src/common/team_identity.py`. React code must use
`src/frontend/src/lib/teamIdentity.ts`.

## Rules

- Source collectors must normalize provider names through this contract before
  writing any local payload.
- Match folder IDs must be composed from canonical slugs.
- `summary.json.ai_summary.injuries` and
  `summary.json.ai_summary.confirmed_tactics` must use canonical slugs.
- API and UI consumers must not split match IDs on every underscore to infer
  teams.
- Unknown names may pass through as unknown strings during exploratory dry-runs,
  but write-mode collectors must report unresolved identities before writing.

## Consequences

- Active fixture slugs now resolve for all 19 current match folders.
- The project display names align with current active `summary.json` metadata,
  including `Czech Republic`, `Turkey`, and
  `Democratic Republic of the Congo`.
- Provider variants remain accepted as aliases, not independent team names.
- T-034, T-036, T-038, and T-039 can proceed without creating new local alias
  tables.

## Verification

- `python3 -m json.tool data/reference/team_identity.json`
- `python3 -m compileall -q src`
- Custom identity audit for all 19 active fixtures.
- `npm --prefix src/frontend run build`
