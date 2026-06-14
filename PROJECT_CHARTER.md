# Project Charter - FIFA World Cup 2026 Dashboard

Owner: Orchestrator agent
Status: Living document
Last updated: 2026-06-14
Profile: software-app

## Stack

How this project is built and verified. The verify command is this project's definition of "reproducible" (it varies by profile — see profiles/ in the framework).

- Language / runtime: Python 3.10+
- Package / environment manager: pip / uv
- Build command: python -m py_compile src/**/*.py
- Test command: python compile_static_fixtures.py --dry-run
- Verify command: python compile_static_fixtures.py --dry-run

## Mission

Build a high-performance web application tracking the live FIFA World Cup 2026. The application filters out media noise by combining advanced data science metrics with programmatic NLP news summaries. It serves a targeted user base (friends and family).

## Non-goals

- Do not let decisions live only in chat.
- Do not duplicate living-document sections.
- Do not rebuild a complex full-stack Next.js/FastAPI application if Streamlit covers the requirements.

## Questions

- Q1. How will we combine NLP summaries from Google AI Studio with BigQuery stats?
- Q2. How exactly will the custom CSS rendering work for the bracket?

## Phases

### Phase 0 - Initialization (Completed)
- Exit criteria met. Consolidated legacy codebases, and framework compliance check passes.

### Phase 1 - Static Pre-calculation Engine (Completed)
- Exit criteria met. Static pre-calculation data compiling to `data/matches/` via model integrations.

### Phase 2 - Dashboard UI (Completed)
- Exit criteria met. Streamlit UI with the wood board symmetrical bracket wall, team analysis panel (with side-by-side comparison mode), and match tactical previews are fully complete and running locally.

### Phase 3 - Ingestion & Sync
- Connect local group standings data to live Nestor PostgreSQL/NestJS backend standings once deployed.

## Team

Roles are defined in AGENTS.md.

## Success Criteria

- App successfully displays brackets, standings, and deep analytics.
- Execution costs are kept low by pre-calculating fixtures.

## Decision Log

| Date | Decision | Owner | File |
|---|---|---|---|
| 2026-06-14 | Project initialized from AI Workflow Framework | Orchestrator | docs/decisions/20260614_DEC001_charter_v1.md |

## Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Scope remains too vague | High | Orchestrator updates this charter before dispatching | Orchestrator |
| BigQuery Costs | Medium | Pre-calculate outputs via static compilation | Data Pipeline Engineer |
