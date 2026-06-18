# Developer Playbook & SOP

## FIFA World Cup 2026 Dashboard

Last updated: 2026-06-18

This playbook describes the current local architecture and operating workflow.
Older Streamlit instructions are legacy/reference unless explicitly called out.

## 1. Current Architecture

### Active Application

- Frontend: React/Vite/TypeScript in `src/frontend/`.
- Backend: FastAPI in `src/api/main.py`.
- Container: `Dockerfile` builds the React app, copies `dist/` into
  `src/api/static`, and serves the SPA plus API from Uvicorn on port `8080`.
- Cloud deployment: `cloudbuild.yaml` builds and deploys the image to Cloud Run.

### Legacy Reference

- Streamlit code remains in `src/app/`.
- Treat it as reference/legacy code unless a new decision restores it as an
  active runtime.

## 2. Local Verification

Run from the repository root:

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
```

Combined verify command:

```bash
python3 -m compileall -q src && npm --prefix src/frontend run build
```

This verifies local Python syntax and frontend production build only. It does
not verify:

- BigQuery credentials.
- Cloud Run live state.
- `worldcup26.ir` freshness.
- Remote `accionar.xyz` static assets.

## 3. Running Locally

Frontend dev server:

```bash
npm --prefix src/frontend install
npm --prefix src/frontend run dev
```

Backend API server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
```

The React app resolves `localhost` and `127.0.0.1` to
`http://localhost:8080`. Non-local hosts use the configured Cloud Run URL in
`src/frontend/src/App.tsx`.

## 4. Data Flows

### Schedule and Match Metadata

- Source files: `data/matches/{match_id}/summary.json`.
- API route: `/api/schedule`.
- UI consumers: Overview fixtures, Match Analysis dropdown/header.

Each active fixture folder ends in `_2026`. Numeric folders such as `1001`,
`1002`, and `1003` are legacy/stub data and are not included in `/api/schedule`.

### Match Editorial Content

- Source files: `data/matches/{match_id}/summary.json`.
- API route: `/api/match/{match_id}/summary`.
- UI consumers: tactical headline, injury updates, coaching/tactics cards,
  pitch formation, key match insights.

Treat `ai_summary` as curated editorial content. Do not overwrite it with
generated output unless a dry-run/diff has been reviewed.

### Forecast and Team Profile Metrics

- Source files: `data/matches/{match_id}/metrics.json`.
- API route: `/api/match/{match_id}/metrics`.
- UI consumers: outcome probability, exact scores, team radar,
  Squad & Style Comparison.

Current active metric files contain:

- `dixon_coles_forecast`
- `score_probabilities`
- `team_metrics`

Runtime API augmentation adds:

- `elo_ratings`
- `monte_carlo_projections`
- `viz_proxies`

Important: active `metrics.json` files are not the older BigQuery event-frame
payloads. The old BigQuery-style schema appears in legacy numeric folders.

T-026 provenance truth:

- Current Elo ratings are local hardcoded defaults.
- Current Dixon-Coles output is an Elo-derived Poisson forecast with low-score
  adjustment.
- Current `40/30/30` values are default fallback values.
- Current progression projections are deterministic Elo estimates, not Monte
  Carlo simulations.
- See `docs/model_provenance.md` before changing labels or model claims.

### Standings and Bracket

- Static fallback: `data/bracket/grid_state.json`.
- Live sources:
  - `https://worldcup26.ir/get/groups`
  - `https://worldcup26.ir/get/games`
- API route: `/api/standings`.
- UI consumer: `StandingsTab`.

The API uses `curl -s -k` via subprocess because the external API has SSL
behavior that fails under normal Python HTTP clients.

### StatsBomb Proxy Visualizations

- API route: `/api/visualizations/{match_id}/{viz_type}`.
- Backing source: BigQuery historical StatsBomb proxy matches.
- UI disclosure: these are proxy/historical event plots, not live 2026 event
  data.

These routes need Google Cloud credentials locally. Build verification does not
prove they work.

## 5. Pipeline Procedures

### Update Local Standings Fallback

```bash
python3 src/pipeline/update_live_standings.py
```

Verify changes in:

```bash
data/bracket/grid_state.json
```

### Baseline Preview and Last-Minute Briefing Generation

Before a match can receive a briefing, it needs a baseline fixture folder:

```text
data/matches/{match_id}/summary.json
data/matches/{match_id}/metrics.json
```

For games that are not already in `data/matches/`, use the planned active
fixture discovery flow:

```bash
python3 src/pipeline/discover_active_fixtures.py --dry-run --window-hours 24
python3 src/pipeline/discover_active_fixtures.py --write --window-hours 24
```

Source order for baseline stubs:

- primary: `https://worldcup26.ir/get/games`
- fallback cache: `/tmp/games.json`
- existing local files: preserve existing `summary.json` and `metrics.json`
- team identity: shared registry from T-027 once implemented

Stub data rules:

- `summary.metadata` comes from the schedule source: teams, date, time, venue,
  and stage.
- `summary.ai_summary` uses explicit "preview pending" placeholders; it must
  not invent tactical news.
- `metrics.dixon_coles_forecast` uses the current-compatible default 40/30/30
  shape and must be labeled `default_forecast` in the manifest.
- `metrics.score_probabilities` uses the current-compatible six fallback
  scorelines and must be labeled `default_forecast` in the manifest.
- `metrics.team_metrics` contains the two team keys with empty objects until
  T-031 fills or labels them.
- Stubs must be labeled `baseline_stub`.

Current caution: do not run baseline preview generation blindly.

```bash
python3 src/pipeline/generate_match_previews.py
```

`summary.json` is the baseline curated preview layer. It is not the
last-minute briefing layer, and it must not be overwritten to create matchday
updates.

Before using `generate_match_previews.py` again, Phase 5 requires:

- dry-run mode
- diff preview
- explicit overwrite/preserve rules for curated `summary.json`
- validation output for missing Elo, empty `team_metrics`, and default forecasts

Last-minute matchday updates are planned as a separate artifact:

```text
data/matches/{match_id}/briefing.json
```

The T-025 plan is documented in:

```bash
docs/last_minute_briefing_plan.md
```

Future implementation should use a separate command similar to:

```bash
python3 src/pipeline/generate_match_briefings.py --dry-run --window-hours 3
python3 src/pipeline/generate_match_briefings.py --write --match-id england_croatia_2026
```

Required behavior:

- dry-run by default
- explicit write mode
- write only `briefing.json`
- preserve `summary.json` and `metrics.json`
- emit source/freshness/data-quality validation before writes
- use the T-035 source policy for web/news collection
- treat fresh last-minute analysis as the 3-hour window before the first match of
  the daily `jornada`

### Source-Backed Research Intake

The intended direction is AI-assisted source-backed matchday research. T-035 is
complete and approves browser automation/scraping with source metadata retained.

Before building scraping, browser automation, official API integration, or
paid-provider ingestion, follow:

- `docs/ai_research_source_policy.md`
- the 3-hour `jornada` freshness window
- source metadata fields and source-set retention rules
- review/publication gates
- the storage target for `web_researched` facts

Every current injury, lineup, roster, suspension, manager, tactical, or metric
claim produced by the future collector should carry a URL/path, source name,
retrieval time, status, and review state.

### Legacy BigQuery Static Compilation

`src/pipeline/compile_static_fixtures.py` writes the older BigQuery-heavy
metrics schema for numeric match IDs. It is not the current active fixture
pipeline for the 19 `_2026` match folders.

## 6. Deployment Procedures

### Cloud Run

From the repository root:

```bash
gcloud builds submit --config cloudbuild.yaml .
```

This builds the Docker image, pushes it, and deploys Cloud Run service
`fifa-2026-dashboard` in `us-central1`.

After deploy, verify:

```bash
curl -s https://fifa-2026-dashboard-80399171028.us-central1.run.app/health
curl -s https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/schedule
```

Then manually smoke-check:

- Overview loads.
- Match Analysis loads at least one current fixture.
- Standings tab loads.
- A proxy visualization either renders or reports a clear credential/source
  failure.

### accionar.xyz

Current docs need a separate refresh before treating this path as authoritative.
Open question: decide whether `accionar.xyz` should host static React assets
directly, embed Cloud Run, or keep both options.

Until that decision is updated, distinguish:

- Cloud Run application state.
- Static asset state under `accionar.xyz/dashboards/fifa-2026/`.
- Portfolio iframe/CSP state.

## 7. Common Pitfalls

- Docs may still contain old Streamlit assumptions. Trust `PROJECT_CHARTER.md`
  first.
- `summary.json` is curated editorial content; generation scripts can overwrite
  it if not made safe.
- Some active fixtures currently have empty `team_metrics`.
- Some active forecasts currently use default `40/30/30` fallback outputs.
- Multi-word team names are fragile in current parsing paths.
- Current "Monte Carlo" projections are deterministic Elo-based estimates, not
  a verified tournament-path simulation.
- BigQuery visualizations need credentials and use historical proxy matches.
- The project should move toward source-backed AI research under the approved
  T-035 source policy.

## 8. Documentation Update Rule

For any change that affects architecture, schema, model interpretation, data
source provenance, deployment, or agent responsibility:

1. Update `TASKS.md`.
2. Update `STATUS.md`.
3. Update `docs/phase_plan.md` if phase scope or ownership changes.
4. Add a decision in `docs/decisions/` when the change is durable.
5. Add a handoff in `docs/handoffs/` when a phase boundary or specialist
   deliverable completes.
