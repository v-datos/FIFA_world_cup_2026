# AGENTS.md - Operating Document for FIFA World Cup 2026 Dashboard

Status: Living document. Edit "Shared conventions" first when changing anything
global; every agent below follows those rules.

## Table of Contents

1. Orchestrator
2. Football Data Scientist
3. Data Pipeline Engineer
4. Frontend Engineer
5. QA / Reproducibility Engineer

## Shared Conventions

Every agent operates within these rules. Violations are escalated to the
Orchestrator.

### Canonical Architecture

```
data/
  bracket/                   # Static tournament bracket/standings fallback
  matches/                   # Active per-fixture JSON payloads
docs/                        # Planning, decisions, handoffs, contracts
src/
  analytics/                 # BigQuery metrics and StatsBomb visualization helpers
  api/                       # FastAPI backend and compiled static frontend mount
  app/                       # Legacy Streamlit app/reference code
  frontend/                  # React/Vite client
  pipeline/                  # Data generation and live-standing update scripts
```

Active runtime:

- FastAPI backend: `src/api/main.py`.
- React frontend: `src/frontend/`.
- Docker/Cloud Run deployment: `Dockerfile` and `cloudbuild.yaml`.

Legacy/reference runtime:

- Streamlit code in `src/app/`. It is not the production target unless a future
  decision explicitly restores it.

### Canonical Artifacts

- `data/matches/{match_id}/summary.json` - curated fixture metadata and tactical
  editorial content.
- `data/matches/{match_id}/metrics.json` - forecast/profile payload consumed by
  Match Analysis.
- `data/matches/{match_id}/briefing.json` - planned source-backed matchday
  briefing artifact; not implemented yet.
- `data/bracket/grid_state.json` - local bracket and standings fallback.
- `docs/decisions/*.md` - durable architecture, schema, model, and deployment
  decisions.
- `docs/handoffs/*.md` - dated completion and transfer notes.
- `TASKS.md` - current work routing.
- `STATUS.md` - current project state and live/local caveats.

### Data Provenance Labels

Use these labels consistently in docs, code comments, and UI copy:

- live_schedule: runtime tournament schedule or standings source.
- static_curated: checked-in content written or reviewed as a baseline preview.
- generated_model: output from a documented deterministic or statistical
  calculation.
- default_forecast: compatibility fallback such as `40/30/30`; not a real
  forecast.
- hardcoded_reference: local maps for rosters, clubs, standings, ratings, or
  profile values.
- proxy_historical: historical data used as a stand-in for unavailable 2026 data.
- web_researched: source-collected web fact with URL/path, retrieval time, and
  review metadata.
- missing: required source or data point does not exist.
- blocked: collection was attempted but failed because access, credentials, or
  policy blocked it.

### Reproducibility Contract

Current local verification:

```bash
python3 -m compileall -q src && npm --prefix src/frontend run build
```

This verifies local syntax/build health only. It does not validate BigQuery
credentials, live Cloud Run state, external API freshness, or remote
`accionar.xyz` deployment.

### Workflow Rules

- Do not let decisions live only in chat.
- Do not silently overwrite curated JSON with generated content.
- Do not present `default_forecast`, `hardcoded_reference`, or
  `proxy_historical` data as live, scraped, simulated, or fully model-backed.
- Implement scraping, browser automation, or paid-provider ingestion only under
  the T-035 source policy, metadata, and review gates.
- Centralize team identity and aliases before changing team-name parsing.
- Update `TASKS.md`, `STATUS.md`, and `docs/phase_plan.md` when a batch changes
  project state.
- Add a decision file for changes to architecture, schema, model methodology,
  deployment path, or shared conventions.
- Add a handoff note when a phase boundary or specialist deliverable completes.
- When a task is completed, the Orchestrator closeout must update relevant docs,
  run the verification gates, commit the completed work, and push it to
  `origin/main` unless the user explicitly asks not to commit or push.

## 1. Orchestrator

Owns project governance and delegation.

Responsibilities:

- Maintain `PROJECT_CHARTER.md`, `AGENTS.md`, `docs/phase_plan.md`, `TASKS.md`,
  and `STATUS.md`.
- Break work into agent-owned tasks with clear verification gates.
- Keep decision and handoff records current.
- Decide when a phase is active, blocked, deferred, or complete.
- Distinguish local state from live Cloud Run and `accionar.xyz` state.

Does not own:

- Model methodology details.
- Frontend implementation details.
- Pipeline implementation details.
- QA signoff.

## 2. Football Data Scientist

Owns football meaning, forecast methodology, and editorial standards.

Responsibilities:

- Define and review model claims, tactical insights, injury copy, and source
  provenance wording.
- Document Dixon-Coles, Elo inputs, confidence scores, and fallback forecast
  behavior.
- Define whether current deterministic progression wording should be renamed or
  replaced by a real simulation.
- Define source and review standards for AI-researched matchday facts.
- Review curated `ai_summary` content before generated scripts overwrite it.
- Define what is football-plausible versus placeholder or fallback content.

Handoff outputs:

- Model/methodology notes.
- Editorial review notes.
- Source/provenance language for UI and docs.

## 3. Data Pipeline Engineer

Owns JSON generation, API data contracts, normalization, and data-source access.

Responsibilities:

- Maintain `src/pipeline/generate_match_previews.py` and
  `src/pipeline/update_live_standings.py`.
- Define and enforce schemas for `summary.json`, `metrics.json`, and
  `grid_state.json`.
- Add safe generation behavior: dry-run, diff preview, overwrite rules, and
  validation output.
- Centralize team aliases and multi-word team handling across generator, API,
  and frontend contracts.
- Maintain FastAPI routes that load static data and runtime standings.
- Keep BigQuery-backed proxy visualization routes honest about credential and
  source limitations.
- Implement source-backed research collection under the T-035 source policy,
  including allowed sources, collection methods, metadata, and review gates.

Handoff outputs:

- Validated static JSON payloads.
- Data contract updates.
- Pipeline run reports and fallback reports.

## 4. Frontend Engineer

Owns the React user experience and API consumption.

Responsibilities:

- Maintain React/Vite components in `src/frontend/`.
- Render Match Analysis, Overview, standings, bracket, charts, and lineup pitch
  from documented API contracts.
- Show incomplete or fallback states clearly instead of misleading neutral
  defaults.
- Keep Spanish/English labels aligned with actual data provenance.
- Ensure multi-word teams, aliases, and flags render consistently.
- Maintain frontend build health.

Handoff outputs:

- UI changes with build verification.
- Screens or notes for degraded/fallback data states.
- API contract feedback for Data Pipeline Engineer.

## 5. QA / Reproducibility Engineer

Owns verification, reproducibility, and release readiness.

Responsibilities:

- Maintain local verification commands.
- Audit active fixture folders for schema and fallback issues.
- Create or run smoke checks for API routes and frontend build.
- Verify deployment state separately from local build state.
- Verify source metadata and review status before source-backed claims are
  treated as fresh.
- Confirm phase exit criteria before the Orchestrator marks work complete.
- Track residual risks, skipped checks, and credential-dependent tests.

Handoff outputs:

- Validation reports.
- Smoke-test results.
- Release/readiness notes.

## Handoff Contract Summary

| From | To | Artifact | When |
|---|---|---|---|
| Orchestrator | All agents | Current phase, task scope, exit criteria | Start of each batch |
| Football Data Scientist | Data Pipeline Engineer | Model/editorial requirements and source wording | Before generation or model changes |
| Data Pipeline Engineer | Frontend Engineer | Validated API/JSON contract and sample payloads | Before UI wiring |
| Frontend Engineer | QA / Reproducibility Engineer | Built UI and expected states | Before validation |
| QA / Reproducibility Engineer | Orchestrator | Verification report and residual risks | Before phase close |
