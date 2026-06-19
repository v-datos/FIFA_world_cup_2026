# T-042 Handoff - Live Deployment Execution and Docker Build Fix

Date: 2026-06-19
Owners: Orchestrator / Data Pipeline Engineer

## Summary

Executed the live Cloud Run deployment that T-029 flagged as a separate operator
task. Cloud Run is now current and verified; `accionar.xyz` needs a browser
confirmation; one schedule-fallback follow-up (T-043) was filed.

## Root Cause of the Live Drift

Cloud Run was frozen at revision `fifa-2026-dashboard-00017-6z7` (2026-06-17),
which predates the T-027 team identity contract (2026-06-18). The Docker
`frontend-builder` stage could not build the frontend because
`src/frontend/src/lib/teamIdentity.ts` imports the repo-canonical
`data/reference/team_identity.json` via `../../../../data/...`, a path outside
`src/frontend/` that the stage did not copy. `tsc -b` raised TS2307 and
`npm run build` exited non-zero, failing Cloud Build before any push or deploy.
No deploy had been attempted since T-027, so the failure went unnoticed.

The local gate `npm --prefix src/frontend run build` did not catch this because
it runs in the real repo where `data/` is a sibling of `src/frontend/`.

## Fix (DEC023)

`Dockerfile` `frontend-builder` stage now mirrors the repo layout:

- `WORKDIR /build/src/frontend`
- `COPY data/reference/team_identity.json /build/data/reference/team_identity.json`
- final stage copies assets from `/build/src/frontend/dist`

The single canonical contract stays at `data/reference/team_identity.json`;
duplicating it into the frontend was rejected (it is shared with the Python
consumers by DEC012).

## Release Signoff

```
Date/time:        2026-06-19 ~20:38-20:46 UTC
Operator:         Orchestrator (vincent.frias@gmail.com)
Git commit:       ca4ad66 (Docker fix + in-progress docs)
Cloud project:    midyear-castle-328020
Cloud Run service: fifa-2026-dashboard (us-central1)
Pre-deploy revision:  fifa-2026-dashboard-00017-6z7  (rollback anchor)
Post-deploy revision: fifa-2026-dashboard-00018-tm5  (100% traffic)
Cloud Build id/status: 88ef8a94 / SUCCESS (7m17s)

Local checks:
- python3 -m compileall -q src:        PASS
- npm --prefix src/frontend run build: PASS (unchanged; Vite chunk warning only)
- git diff --check:                    clean

Cloud Run checks (revision 00018, unauthenticated):
- /health:                             200 {"status":"ok"}
- /api/schedule:                       200; 20 matches; lifecycle + full keys
- /api/match/brazil_haiti_2026/summary: 200 (was 404)
- /api/match/brazil_haiti_2026/metrics: 200; data_quality; MC rating_source
                                        world_football_elo @10000; Brazil
                                        squad_market_value source web_researched
- /api/standings:                      200
- Visualization route with credentials: not verified (BigQuery dependent)

accionar.xyz checks:
- Page HTTP status:  200 (portfolio SPA shell, bundle index-DhXZeTZ5.js)
- Rendered dashboard: NOT browser-confirmed (client-side route; expected to
                      iframe the now-updated Cloud Run service)
- Rollback path verified: anchor revision 00017 recorded; not exercised

Residual risks:
- T-043 schedule fallback: worldcup26.ir unreachable (HTTP 000) + no games cache
  in image => /api/schedule source=unavailable with null match_ids; default
  fixture still loads, but the day-view selector listing loses IDs.
- accionar.xyz rendered content needs a hard-refresh/incognito confirmation.
- IAM: deploy could not re-apply allUsers->run.invoker (no run.setIamPolicy);
  existing public binding persists.
Decision: Cloud Run deployment accepted; close T-042; route T-043 next.
```

## Follow-Ups

1. T-043 - schedule fallback should derive `match_id`/teams/lifecycle from local
   `data/matches/*_2026` folders when the live API and cache are unavailable.
2. Browser-confirm `accionar.xyz/dashboards/fifa-2026/` serves revision 00018
   (or re-upload its static bundle if it hosts its own copy instead of embedding
   Cloud Run).
3. T-030 - Streamlit legacy disposition is now unblocked.
