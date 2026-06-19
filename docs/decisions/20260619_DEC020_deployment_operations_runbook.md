# DEC020 - Deployment and Operations Runbook

Date: 2026-06-19

## Status

Accepted.

## Context

The project has moved from its earlier Streamlit/deployment assumptions to a
React/Vite frontend served by FastAPI in a Docker image on Cloud Run. The local
repo has also advanced through lifecycle filtering, real Monte Carlo, World
Football Elo source cache, and Squad & Style field provenance work.

Local verification proves syntax and build health, but it does not prove live
Cloud Run state, `accionar.xyz` routing/static assets, BigQuery credentials, or
external source freshness.

## Decision

Adopt `docs/deployment_operations_runbook.md` and
`docs/deployment_verification_checklist.md` as the current deployment operating
procedure.

Operators must treat these as separate gates:

1. Local syntax/build verification.
2. Optional local API smoke checks.
3. Optional local Docker image/container smoke checks.
4. Cloud Run build, deploy, status snapshot, smoke, and rollback checks.
5. `accionar.xyz` route/static/iframe/browser verification.

The runbook must not claim live deploy success unless the remote smoke checks
are actually run and recorded.

## Current Live Finding

Read-only checks during T-029 showed Cloud Run was healthy at `/health` after a
cold-start delay, but stale relative to local code:

- `/api/schedule` returned 19 fixtures without lifecycle/source-status fields.
- `brazil_haiti_2026` was missing live.
- Older metrics payloads lacked newer `data_quality` and source-cache metadata.
- `accionar.xyz/dashboards/fifa-2026/` returned HTTP 200, but appeared to serve
  an older portfolio/static route rather than a freshly deployed dashboard
  bundle.

## Consequences

- T-029 completes documentation and verification procedure work, not a live
  redeploy.
- A future deployment task must rebuild and redeploy Cloud Run before claiming
  that live users see T-037/T-039/T-040/T-038 behavior.
- `accionar.xyz` must be verified separately after Cloud Run passes.
- Deployment status updates must preserve local-vs-live distinctions.

## Verification

- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
- `git diff --check`
- Read-only Cloud Run and `accionar.xyz` HTTP checks recorded in T-029 handoff
