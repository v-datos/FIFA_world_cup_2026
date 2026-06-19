# T-029 Handoff - Deployment and Operations Runbook Refresh

Date: 2026-06-19
Owners: Orchestrator / QA / Reproducibility Engineer

## Summary

T-029 is complete as a documentation and verification-procedure task.

The project now has a current deployment runbook and a QA verification checklist
for the React/Vite + FastAPI + Docker + Cloud Run + `accionar.xyz` architecture.
No deployment was performed during this task.

## Added

- `docs/deployment_operations_runbook.md`
- `docs/deployment_verification_checklist.md`
- `docs/decisions/20260619_DEC020_deployment_operations_runbook.md`

## Updated

- `TASKS.md`
- `STATUS.md`
- `docs/phase_plan.md`
- `docs/data_contracts.md`
- `docs/DEVELOPER_PLAYBOOK.md`

## Local Verification

Commands run:

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
git diff --check
```

Results:

- Python compile passed.
- Frontend build passed with the existing Vite large-chunk warning.
- Diff whitespace check passed after cleanup.

QA also ran an in-process API smoke check for:

- `health()`
- `get_schedule()`
- `get_match_summary("brazil_haiti_2026")`
- `get_match_metrics("brazil_haiti_2026")`

## Read-Only Live Checks

These checks were read-only and did not modify Cloud Run or `accionar.xyz`.

Cloud Run:

```bash
curl -sS -m 60 -i https://fifa-2026-dashboard-80399171028.us-central1.run.app/health
curl -sS -m 60 -i https://fifa-2026-dashboard-80399171028.us-central1.run.app/
curl -sS -m 30 -i https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/schedule
curl -sS -m 20 -i https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/match/brazil_haiti_2026/metrics
curl -sS -m 20 -i https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/match/france_senegal_2026/metrics
```

Observed:

- `/health` returned HTTP 200 with `{"status":"ok"}` after cold-start delay.
- `/` returned HTTP 200 and served a React bundle last modified
  2026-06-17.
- `/api/schedule` returned HTTP 200 but only 19 fixtures, with no lifecycle or
  source-status fields.
- `/api/match/brazil_haiti_2026/metrics` returned HTTP 404.
- `/api/match/france_senegal_2026/metrics` returned HTTP 200 but lacked newer
  `data_quality` and source-cache metadata.

`accionar.xyz`:

```bash
curl -sS -m 20 -i https://accionar.xyz/dashboards/fifa-2026/
```

Observed:

- HTTP 200.
- Response looked like the portfolio shell/static route last modified
  2026-06-15, not a freshly deployed standalone dashboard bundle.
- CSP allows the Cloud Run dashboard frame URL.

## Conclusion

Local code is ahead of live deployment. Cloud Run is reachable, but stale
relative to the current repo. `accionar.xyz` also needs separate verification
after any Cloud Run redeploy.

## Residual Risks

- BigQuery/StatsBomb visualization routes were not live-verified.
- Cloud Run redeploy still needs an operator with Google Cloud credentials.
- `accionar.xyz` route strategy remains operationally separate: operators must
  verify whether it should embed Cloud Run or serve a static bundle.
- External schedule and source cache freshness can drift between deploy time
  and matchday.

## Next Recommended Step

Run a deployment execution task only when the operator is ready to rebuild and
smoke-test Cloud Run, then verify `accionar.xyz`.

Project routing after T-029:

1. T-033 - Briefing API and Match Analysis Freshness UI
2. T-031 - Active Match Metrics Completion
3. T-030 - Streamlit Legacy Disposition
