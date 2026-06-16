# Project Charter - FIFA World Cup 2026 Dashboard

Owner: Orchestrator agent
Status: Living document
Last updated: 2026-06-14
Profile: software-app

## Stack

How this project is built and verified. The verify command is this project's definition of "reproducible" (it varies by profile — see profiles/ in the framework).

- Language / runtime: Python 3.11+ / Node.js 20+
- Package / environment manager: pip / uv / npm
- Build command: python -m py_compile src/**/*.py && npm --prefix src/frontend run build
- Test command: python compile_static_fixtures.py --dry-run
- Verify command: python -m py_compile src/**/*.py && npm --prefix src/frontend run build

## Mission

Build a high-performance web application tracking the live FIFA World Cup 2026. The application filters out media noise by combining advanced data science metrics with programmatic NLP news summaries. It serves a targeted user base (friends and family).

## Non-goals

- Do not let decisions live only in chat.
- Do not duplicate living-document sections.
- Do not rebuild a complex full-stack Next.js/FastAPI application if Streamlit covers the requirements. (Obsolete: streamlit replaced due to layout limitations and user approval)

## Questions

- Q1. How will we combine NLP summaries from Google AI Studio with BigQuery stats?
- Q2. How exactly will the custom CSS rendering work for the bracket?

## Phases

### Phase 0 - Initialization (Completed)
- Exit criteria met. Consolidated legacy codebases, and framework compliance check passes.

### Phase 1 - Static Pre-calculation Engine (Completed)
- Exit criteria met. Static pre-calculation data compiling to `data/matches/` via model integrations.

### Phase 2 - Streamlit Dashboard UI (Completed)
- Exit criteria met. Streamlit UI with the wood board symmetrical bracket wall, team analysis panel, and match tactical previews complete.

### Phase 3 - Ingestion & Sync (Dismissed)
- Connect local group standings data to live Nestor PostgreSQL standings. (Dismissed on 2026-06-16).

### Phase 4 - Decoupled React Client & FastAPI REST Backend Migration (Completed)
- Exit criteria met. FastAPI REST backend implements data routes and serves compiled frontend assets. React Vite client replaces Streamlit with high-performance interactive Recharts and coordinate-based lineup pitches.

## Team

Roles are defined in AGENTS.md.

## Success Criteria

- App successfully displays brackets, standings, and deep analytics.
- Execution costs are kept low by pre-calculating fixtures.

## Decision Log

| Date | Decision | Owner | File |
|---|---|---|---|
| 2026-06-14 | Project initialized from AI Workflow Framework | Orchestrator | docs/decisions/20260614_DEC001_charter_v1.md |
| 2026-06-15 | Deployed Streamlit App to Cloud Run & Configured AI Previews | Orchestrator | docs/decisions/20260615_DEC002_deployment_and_previews.md |
| 2026-06-16 | Dismissed Phase 3 Standings Sync & Restricted Match Previews to Active Date | Orchestrator | docs/decisions/20260616_DEC003_dismiss_phase3_and_limit_previews.md |
| 2026-06-16 | Decoupled React & FastAPI Migration with Interactive Visualizations | Orchestrator | docs/decisions/20260616_DEC005_decoupled_react_migration.md |

## Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Scope remains too vague | High | Orchestrator updates this charter before dispatching | Orchestrator |
| BigQuery Costs | Medium | Pre-calculate outputs via static compilation | Data Pipeline Engineer |
