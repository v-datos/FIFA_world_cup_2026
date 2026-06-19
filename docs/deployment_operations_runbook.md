# Deployment and Operations Runbook

Last updated: 2026-06-19
Task: T-029 - Deployment and Operations Runbook Refresh
Owner: Orchestrator / QA / Reproducibility Engineer

## Purpose

This runbook separates local build confidence from live deployment confidence
for the current React/Vite + FastAPI application.

Do not treat local verification as proof that Cloud Run or
`accionar.xyz/dashboards/fifa-2026/` is current. Those are separate deployment
surfaces and must be checked independently.

## Current Deployment Architecture

Active runtime:

- React/Vite frontend in `src/frontend/`.
- FastAPI backend in `src/api/main.py`.
- Docker image built by `Dockerfile`.
- Cloud Run deployment configured by `cloudbuild.yaml`.

Container behavior:

1. Docker stage `frontend-builder` runs `npm run build` in `src/frontend/`.
2. The final Python image installs `requirements.txt` and copies the repo.
3. Built React files are copied into `/app/src/api/static`.
4. FastAPI mounts `src/api/static` at `/` if that directory exists.
5. Uvicorn serves API routes and static frontend assets on port `8080`.

Cloud Build target:

| Item | Value |
|---|---|
| Image | `gcr.io/midyear-castle-328020/fifa-2026-dashboard` |
| Cloud Run service | `fifa-2026-dashboard` |
| Region | `us-central1` |
| Port | `8080` |
| Liveness probe | `/health` |
| Public Cloud Run URL currently used by frontend | `https://fifa-2026-dashboard-80399171028.us-central1.run.app` |

`accionar.xyz` behavior:

- Public dashboard URL:
  `https://accionar.xyz/dashboards/fifa-2026/`.
- The current frontend code uses the Cloud Run API URL for any non-local host.
- The route may serve the portfolio shell or a static dashboard bundle depending
  on the website deployment. Verify it separately from Cloud Run.

## Local Verification

Run from the repository root:

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
```

Combined gate:

```bash
python3 -m compileall -q src && npm --prefix src/frontend run build
```

This proves:

- Python source under `src/` has no syntax errors.
- TypeScript and Vite can produce a production frontend bundle.

This does not prove:

- Cloud Run has the latest image.
- `accionar.xyz` has the latest shell/static assets.
- BigQuery credentials work.
- StatsBomb proxy visualization routes work.
- External APIs are fresh or reachable.
- Source-backed research caches were refreshed.

Known local warnings:

- Vite currently emits a large-chunk warning; the build still passes.
- Direct API imports can emit Matplotlib/fontconfig cache warnings when the user
  home cache is not writable.
- Direct API imports can emit Streamlit cache warnings because legacy/reference
  modules are imported outside Streamlit.

## Local API Smoke

Optional in-process smoke:

```bash
python3 -c 'from src.api.main import health, get_schedule, get_match_summary, get_match_metrics; print(health()); print(get_schedule().keys()); print(get_match_summary("brazil_haiti_2026")["briefing_status"]); m=get_match_metrics("brazil_haiti_2026", simulation_count=10000, seed=20260618); print(m["data_quality"].keys())'
```

Optional server smoke:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/api/schedule
curl -fsS http://localhost:8080/api/match/brazil_haiti_2026/summary
curl -fsS "http://localhost:8080/api/match/brazil_haiti_2026/metrics?simulation_count=10000&seed=20260618"
curl -fsS http://localhost:8080/api/standings
```

Expected current local signals:

- `/health` returns `{"status":"ok"}`.
- `/api/schedule` returns lifecycle/source-status fields and a briefing window.
- `brazil_haiti_2026` exists locally.
- `brazil_haiti_2026` metrics include `data_quality`,
  `team_metric_source_cache`, `team_metric_sources`, Elo provenance, and Monte
  Carlo metadata.

BigQuery caveat:

- `/api/visualizations/{match_id}/{viz_type}` needs Google Cloud/BigQuery
  credentials and historical StatsBomb proxy data access. Local build success
  does not validate these routes.

## Docker Verification

Build a local image:

```bash
docker build -t fifa-2026-dashboard:local .
```

Run it:

```bash
docker run --rm -p 8080:8080 fifa-2026-dashboard:local
```

If port `8080` is busy:

```bash
docker run --rm -p 8081:8080 fifa-2026-dashboard:local
```

Smoke the container:

```bash
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/api/schedule
curl -fsS "http://localhost:8080/api/match/brazil_haiti_2026/metrics?simulation_count=10000&seed=20260618"
```

Pass criteria:

- Uvicorn starts and stays running.
- `/health` returns JSON.
- API routes return JSON, not the React static fallback.
- Root path serves the compiled React app.

## Cloud Run Deployment

Pre-deploy snapshot:

```bash
gcloud config get-value project
gcloud run services describe fifa-2026-dashboard --region us-central1 --format="table(metadata.name,status.url,status.latestReadyRevisionName,status.traffic[].revisionName,status.traffic[].percent)"
gcloud run revisions list --service fifa-2026-dashboard --region us-central1 --limit 5
```

Record:

- Google Cloud project id.
- Service URL.
- Current ready revision.
- Traffic split.
- Last known `/health`, `/api/schedule`, representative summary, and
  representative metrics responses.

Deploy:

```bash
gcloud builds submit --config cloudbuild.yaml .
```

Post-deploy snapshot:

```bash
gcloud builds list --limit 5 --format="table(id,status,createTime,finishTime)"
gcloud run services describe fifa-2026-dashboard --region us-central1 --format="table(metadata.name,status.url,status.latestReadyRevisionName,status.traffic[].revisionName,status.traffic[].percent)"
gcloud run revisions list --service fifa-2026-dashboard --region us-central1 --limit 5
```

Cloud Run smoke:

```bash
RUN_URL="https://fifa-2026-dashboard-80399171028.us-central1.run.app"
curl -fsS "$RUN_URL/health"
curl -fsS "$RUN_URL/api/schedule"
curl -fsS "$RUN_URL/api/match/brazil_haiti_2026/summary"
curl -fsS "$RUN_URL/api/match/brazil_haiti_2026/metrics?simulation_count=10000&seed=20260618"
curl -fsS "$RUN_URL/api/standings"
```

Use the URL from `gcloud run services describe` if it differs from `RUN_URL`.

Pass criteria:

- Latest Cloud Build is `SUCCESS`.
- Latest ready revision matches the intended deployment.
- Traffic is routed to the intended revision.
- `/api/schedule` includes lifecycle/source-status fields.
- `brazil_haiti_2026` routes exist.
- Metrics responses include `data_quality`, T-039 rating provenance, T-037
  Monte Carlo metadata, and T-038 Squad & Style source fields.

## Cloud Run Rollback

If post-deploy smoke fails:

1. Do not update `accionar.xyz`.
2. Capture build id, revision name, status code, and response body.
3. Inspect logs:

```bash
gcloud run services logs read fifa-2026-dashboard --region us-central1 --limit 100
```

4. Route traffic back to the previous healthy revision:

```bash
gcloud run services update-traffic fifa-2026-dashboard --region us-central1 --to-revisions PREVIOUS_REVISION=100
```

5. Re-run `/health`, `/api/schedule`, one summary route, one metrics route, and
   `/api/standings`.
6. Record rollback revision, timestamp, operator, and residual failures.

## accionar.xyz Verification

Public URL:

```text
https://accionar.xyz/dashboards/fifa-2026/
```

Read-only checks:

```bash
curl -I https://accionar.xyz/dashboards/fifa-2026/
curl -sS https://accionar.xyz/dashboards/fifa-2026/ | head
```

Browser checks:

- Page loads without a blank screen.
- If the route embeds Cloud Run, the iframe source points to the current Cloud
  Run URL and the CSP `frame-src` allows it.
- If the route serves a standalone static React bundle, asset paths resolve
  under the correct directory and API calls reach Cloud Run.
- Overview loads current-day not-finished fixtures.
- Match Analysis loads a current fixture.
- Standings loads.
- Console has no API/CORS/static asset errors.

`accionar.xyz` pass criteria:

- The public route serves the intended dashboard surface.
- It references current assets or current Cloud Run iframe/configuration.
- Network calls use the current Cloud Run API.
- The route is not serving an older portfolio shell when the intended release is
  a standalone dashboard bundle.

Rollback for `accionar.xyz`:

- Restore the previous known-good static asset set or portfolio route config.
- Confirm the Cloud Run backend remains healthy.
- Re-run browser checks and asset URL checks.
- Record changed files/assets, timestamp, and operator.

## Current Live Snapshot From T-029

Read-only checks run on 2026-06-19 showed:

- Cloud Run `/health` eventually returned HTTP 200 with `{"status":"ok"}` after
  cold-start delay.
- Cloud Run `/api/schedule` returned HTTP 200 but only 19 fixtures, no
  lifecycle/source-status fields, and no `brazil_haiti_2026`.
- Cloud Run `/api/match/brazil_haiti_2026/metrics` returned HTTP 404.
- Cloud Run `/api/match/france_senegal_2026/metrics` returned HTTP 200 but the
  payload lacked newer `data_quality` and source-cache metadata.
- `accionar.xyz/dashboards/fifa-2026/` returned HTTP 200, but the HTML looked
  like the portfolio shell/static route last modified 2026-06-15 rather than a
  freshly deployed dashboard bundle.

Conclusion:

- Local code is ahead of live Cloud Run and `accionar.xyz`.
- A rebuild/redeploy is required before live users see T-029-adjacent current
  behavior, T-040 lifecycle fields, T-037/T-039 provenance metadata, or T-038
  Squad & Style source states.

## Data and Source Artifact Readiness

Before deployment, decide whether to refresh or preserve:

- `data/source_cache/world_football_elo/latest_ratings.json`
- `data/source_cache/squad_style/latest_metrics.json`
- `data/matches/{match_id}/briefing.json`
- `data/matches/{match_id}/research_cache.json`
- `data/bracket/grid_state.json`

Rules:

- T-032 `briefing.json` is optional and freshness-gated.
- T-036 `research_cache.json` is draft/review-gated and not a production UI
  source yet.
- T-038 source cache is production-readable but partial; missing fields must
  remain missing, not inferred.
- Source caches should not be refreshed during deploy unless the operator
  explicitly wants a new source run and records the output.

## Release Notes Template

Before deploy:

```text
Release candidate:
- Commit:
- Local verification:
- Docker verification:
- Source cache refreshes:
- Known caveats:
- Previous Cloud Run revision:
```

After deploy:

```text
Deployment:
- Build id:
- Cloud Run revision:
- Traffic split:
- Cloud Run smoke:
- accionar.xyz smoke:
- BigQuery visualization status:
- Rollback revision:
- Residual risks:
```
