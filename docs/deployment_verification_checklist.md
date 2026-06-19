# Deployment Verification Checklist

Last updated: 2026-06-19  
Task: T-029 - Deployment and Operations Runbook Refresh  
Owner: QA / Reproducibility Engineer  
Scope: Local reproducibility, container smoke checks, Cloud Run validation, and
`accionar.xyz` live-status verification.

## Purpose

This checklist separates checks that can be run safely in a local workspace from
checks that require Google Cloud credentials, network access, DNS/static hosting
access, or production operator approval.

Do not mark a deployment verified from local build output alone. Local syntax,
frontend build, and in-process API checks prove the repository can build and
serve expected payloads locally; they do not prove Cloud Run, DNS, static asset
cache, BigQuery credentials, or live external data freshness.

## 1. Local Verification Gate

Run from the repository root.

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
```

Combined gate:

```bash
python3 -m compileall -q src && npm --prefix src/frontend run build
```

Expected meaning:

| Check | Pass means | Fail means |
|---|---|---|
| `python3 -m compileall -q src` | Python files under `src/` compile to bytecode. This catches syntax errors. | A Python syntax error or invalid module file exists. Fix before deployment. |
| `npm --prefix src/frontend run build` | TypeScript project build and Vite production bundle complete. | Frontend type-checking or production bundling failed. Fix before deployment. |

Known local warnings:

- Vite currently emits a chunk-size warning for a JavaScript asset over 500 kB.
  This warning does not fail the build by itself.
- Direct API imports may emit Matplotlib cache/fontconfig warnings when the
  user home cache is not writable. Set `MPLCONFIGDIR` to a writable temporary
  directory if this slows smoke checks.
- Direct API imports may emit Streamlit cache warnings because legacy/reference
  modules are imported outside a Streamlit runtime. These warnings do not prove
  a production failure by themselves.

Latest QA local run on 2026-06-19:

| Command | Result | Notes |
|---|---|---|
| `python3 -m compileall -q src` | Pass | No output. |
| `npm --prefix src/frontend run build` | Pass | Existing Vite large-chunk warning only. |

## 2. Optional Local API Smoke Checks

These checks are safe and do not deploy. They verify representative FastAPI
handlers and active fixture payloads.

In-process smoke check:

```bash
python3 -c 'from src.api.main import health, get_schedule, get_match_summary, get_match_metrics; print("health", health()); schedule=get_schedule(); print("schedule", len(schedule.get("matches", [])), schedule.get("schedule_source"), schedule.get("default_match_id")); summary=get_match_summary("brazil_haiti_2026"); print("summary", summary.get("metadata", {}).get("team1"), summary.get("metadata", {}).get("team2"), summary.get("briefing_status", {}).get("freshness_state")); metrics=get_match_metrics("brazil_haiti_2026", simulation_count=10000, seed=20260618); dq=metrics.get("data_quality", {}); print("metrics_keys", sorted(dq.keys())); print("brazil_value_source", dq.get("team_metrics", {}).get("Brazil", {}).get("field_sources", {}).get("squad_market_value_m", {}).get("source_label"))'
```

Expected output shape:

- `health {'status': 'ok'}`
- `schedule` prints a match count, schedule source, and default match id.
- `summary` prints the fixture teams and briefing freshness state.
- `metrics_keys` includes `forecast`, `score_probabilities`, `team_metrics`,
  `elo_ratings`, `monte_carlo_projections`, `radar_metrics`,
  `visualizations`, and source-cache metadata keys.
- For the current T-038 sample, `brazil_value_source` should print
  `web_researched`.

Latest QA in-process smoke on 2026-06-19:

| Route/function | Result | Notes |
|---|---|---|
| `health()` | Pass | Returned `{"status": "ok"}`. |
| `get_schedule()` | Pass | Returned 20 matches, `schedule_source=cache`, default `united_states_australia_2026`. |
| `get_match_summary("brazil_haiti_2026")` | Pass | Returned Brazil vs Haiti with `briefing_status=baseline_only`. |
| `get_match_metrics("brazil_haiti_2026")` | Pass | Returned expected data-quality keys; Brazil squad value source was `web_researched`. |

Optional server smoke:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/api/schedule
curl -fsS http://localhost:8080/api/match/brazil_haiti_2026/summary
curl -fsS "http://localhost:8080/api/match/brazil_haiti_2026/metrics?simulation_count=10000&seed=20260618"
curl -fsS http://localhost:8080/api/standings
```

Interpretation:

- `/health` should return `{"status":"ok"}`.
- `/api/schedule` should return active `_2026` fixture folders plus lifecycle
  metadata and a briefing window object.
- `/api/match/brazil_haiti_2026/summary` should return the baseline summary and
  `briefing_status`.
- `/api/match/brazil_haiti_2026/metrics` should return forecast, score,
  source-cache, Elo, Monte Carlo, visualization, and data-quality payloads.
- `/api/standings` may use live/cache schedule state. A network failure should
  be investigated only if it breaks the route or removes expected fallback
  behavior.

Credential-dependent local routes:

- `/api/visualizations/{match_id}/{viz_type}` needs Google Cloud/BigQuery
  credentials and historical StatsBomb proxy data access. Local build success
  does not validate this route.

## 3. Docker Image and Container Verification

These checks are local and non-destructive to remote infrastructure. They create
a local Docker image and container only.

Build a throwaway local image:

```bash
docker build -t fifa-2026-dashboard:local .
```

Run the container:

```bash
docker run --rm -p 8080:8080 fifa-2026-dashboard:local
```

If port `8080` is already in use:

```bash
docker run --rm -p 8081:8080 fifa-2026-dashboard:local
```

Smoke checks:

```bash
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/api/schedule
curl -fsS "http://localhost:8080/api/match/brazil_haiti_2026/metrics?simulation_count=10000&seed=20260618"
```

For `8081` host mapping, replace `localhost:8080` with `localhost:8081`.

Pass criteria:

- Container starts with Uvicorn and listens on the mapped port.
- `/health` returns `{"status":"ok"}`.
- `/api/schedule` returns JSON rather than a static-file fallback or HTML.
- `/api/match/brazil_haiti_2026/metrics` returns JSON with `data_quality`.
- The React static build is served from the container root path when opened in a
  browser.

Fail criteria:

- Docker build cannot install Node/Python dependencies.
- Container exits before serving Uvicorn.
- API routes return 404/500.
- Root path does not serve the React production bundle.

Network caveat:

- Docker build may need external registry/package access unless dependencies are
  already cached locally.

## 4. Cloud Run Deployment Verification

These checks require Google Cloud credentials, the correct project, and network
access. They were not executed by the T-029 QA local checklist unless explicitly
recorded in a deployment log.

Current configured deployment target from `cloudbuild.yaml`:

| Item | Value |
|---|---|
| Project/image path | `gcr.io/midyear-castle-328020/fifa-2026-dashboard` |
| Cloud Run service | `fifa-2026-dashboard` |
| Region | `us-central1` |
| Port | `8080` |
| Liveness probe | `/health` |

Pre-deploy status snapshot:

```bash
gcloud config get-value project
gcloud run services describe fifa-2026-dashboard --region us-central1 --format="table(metadata.name,status.url,status.latestReadyRevisionName,status.traffic[].revisionName,status.traffic[].percent)"
gcloud run revisions list --service fifa-2026-dashboard --region us-central1 --limit 5
```

Record before deployment:

- Active project id.
- Current service URL.
- Current ready revision.
- Current traffic split.
- Last known healthy `/health`, `/api/schedule`, and Match Analysis fixture
  route responses.

Deploy through the checked-in Cloud Build config:

```bash
gcloud builds submit --config cloudbuild.yaml .
```

Post-build/deploy status:

```bash
gcloud builds list --limit 5 --format="table(id,status,createTime,finishTime)"
gcloud run services describe fifa-2026-dashboard --region us-central1 --format="table(metadata.name,status.url,status.latestReadyRevisionName,status.traffic[].revisionName,status.traffic[].percent)"
gcloud run revisions list --service fifa-2026-dashboard --region us-central1 --limit 5
```

Live service smoke checks:

```bash
curl -fsS https://fifa-2026-dashboard-80399171028.us-central1.run.app/health
curl -fsS https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/schedule
curl -fsS https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/match/brazil_haiti_2026/summary
curl -fsS "https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/match/brazil_haiti_2026/metrics?simulation_count=10000&seed=20260618"
curl -fsS https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/standings
```

If the service URL returned by `gcloud run services describe` differs from the
URL above, use the returned service URL as authoritative.

Cloud Run pass criteria:

- Latest Cloud Build status is `SUCCESS`.
- Cloud Run latest ready revision matches the deployed image.
- Traffic is routed to the intended revision.
- `/health` returns `{"status":"ok"}`.
- `/api/schedule` returns JSON with lifecycle/source status.
- A current Match Analysis summary route returns JSON with `briefing_status`.
- A current metrics route returns JSON with `data_quality`, Elo provenance,
  Monte Carlo metadata, and Squad & Style field source states.
- `/api/standings` returns live or fallback standings without a 500.

Cloud Run failure response:

- Do not update `accionar.xyz` or announce a release if Cloud Run smoke checks
  fail.
- Capture Cloud Build id, revision name, route status code, and response body.
- Check logs:

```bash
gcloud run services logs read fifa-2026-dashboard --region us-central1 --limit 100
```

Rollback expectation:

1. Identify the previous healthy revision from the pre-deploy snapshot.
2. Route 100% traffic back to it:

```bash
gcloud run services update-traffic fifa-2026-dashboard --region us-central1 --to-revisions PREVIOUS_REVISION=100
```

3. Re-run `/health`, `/api/schedule`, one summary route, one metrics route, and
   `/api/standings`.
4. Record the rollback revision, timestamp, operator, and residual failures.

## 5. `accionar.xyz` Live Checklist

These checks require public network access and may require access to the static
hosting/CDN or portfolio configuration. They were not executed by this local QA
checklist unless explicitly recorded.

Canonical public dashboard URL:

```text
https://accionar.xyz/dashboards/fifa-2026/
```

HTTP checks:

```bash
curl -I https://accionar.xyz/dashboards/fifa-2026/
curl -fsS https://accionar.xyz/dashboards/fifa-2026/
```

Browser checks:

- Load `https://accionar.xyz/dashboards/fifa-2026/` in a normal browser window.
- Hard-refresh or use an incognito/private window to avoid stale cached assets.
- Confirm the dashboard loads the current React UI, not a stale Streamlit or
  legacy static page.
- Confirm Overview renders only today's not-finished fixtures by default.
- Confirm Match Analysis loads the current default fixture.
- Confirm the Squad & Style section shows sourced/reference/missing states.
- Confirm the standings tab loads or shows a clear fallback/error state.
- Confirm browser console has no blocking JavaScript errors.
- Confirm network requests target the intended API host.

Static asset checks:

- The HTML should reference current hashed JS/CSS assets.
- Referenced JS/CSS assets should return HTTP 200.
- There should be no stale 404 asset URLs from a previous Vite build.
- Cache headers should not prevent urgent rollback or hotfix visibility.

`accionar.xyz` rollback expectations:

- If it embeds or proxies Cloud Run, first rollback Cloud Run traffic and then
  verify the public page hits the restored revision.
- If it hosts static React assets directly, retain the previous static bundle or
  hosting release so the asset set can be restored.
- After rollback, repeat:
  - page load
  - root HTTP status
  - asset HTTP status
  - `/health` API reachability through the public page's configured API host
  - one current summary route
  - one current metrics route

Do not mark `accionar.xyz` verified from Cloud Run checks alone. The public
domain can fail because of DNS, CDN cache, static asset drift, iframe/CSP
settings, or stale API host configuration even when Cloud Run is healthy.

## 6. Residual Risks and Dependency Boundaries

| Risk | Why local build does not cover it | Required verification |
|---|---|---|
| BigQuery credentials | `compileall` and frontend build do not authenticate to BigQuery. | Run visualization routes with valid Google Cloud credentials and confirm expected proxy images or clear credential errors. |
| Live Cloud Run state | Local build does not prove Cloud Build, image push, revision readiness, traffic split, or service logs. | Use `gcloud builds`, `gcloud run services describe`, `gcloud run revisions list`, live curls, and Cloud Run logs. |
| `accionar.xyz` DNS/static cache | Cloud Run can be healthy while the public URL serves stale assets or a different app path. | HTTP header checks, browser hard-refresh, asset URL checks, and console/network inspection. |
| External source freshness | Runtime can read stale local caches when external sources are unreachable. | Check source cache metadata, schedule source status, World Football Elo cache timestamp, squad/style cache timestamp, and live schedule status. |
| `worldcup26.ir` availability | `/api/schedule` and standings may use cache/fallback when live API fails. | Confirm `schedule_source`, lifecycle counts, and fallback behavior during live smoke checks. |
| Source-backed Squad & Style coverage | T-038 only seeded a partial sample; most fields may still be missing or hardcoded references. | Inspect `/api/match/{id}/metrics.data_quality.team_metrics[team].field_sources` for the fixture being tested. |
| Docker/network dependencies | Local source build can pass while Docker package install fails due to registry/network problems. | Run local Docker build and container smoke checks before Cloud Build when possible. |
| Browser-only failures | API curls can pass while the React UI fails due to asset, routing, CORS, or client-side state issues. | Browser smoke test the Cloud Run service root and `accionar.xyz`. |

## 7. Release Signoff Template

Use this template in the deployment log or handoff note.

```text
Date/time:
Operator:
Git commit:
Cloud project:
Cloud Run service:
Pre-deploy revision:
Post-deploy revision:
Cloud Build id/status:

Local checks:
- python3 -m compileall -q src:
- npm --prefix src/frontend run build:
- Optional local API smoke:
- Optional Docker smoke:

Cloud Run checks:
- /health:
- /api/schedule:
- /api/match/{match_id}/summary:
- /api/match/{match_id}/metrics:
- /api/standings:
- Visualization route with credentials:

accionar.xyz checks:
- Page HTTP status:
- Asset HTTP status:
- Browser UI:
- Console/network:
- Rollback path verified:

Residual risks:
Decision:
```
