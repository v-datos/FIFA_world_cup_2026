# Decision: Framework Rebaseline & Pipeline Hardening

Date: 2026-06-17
Authority: Orchestrator
Status: Decided

## Context

The project evolved from the initial framework/bootstrap and Streamlit dashboard
into a React/Vite frontend served by a FastAPI backend. The operating documents
did not keep up with that migration. As a result, the charter, agent roster,
phase plan, task list, and developer playbook contained stale Streamlit-first
language and did not capture the fragile parts of the current static-data
pipeline.

Recent review found specific issues:

- Active runtime is React/FastAPI, while several docs still describe Streamlit
  as the primary application.
- The 19 active match folders use curated `summary.json` files and lightweight
  forecast/profile `metrics.json` files.
- Legacy numeric folders `1001`, `1002`, and `1003` use a different
  BigQuery-heavy metrics schema.
- Some active fixtures have empty `team_metrics`.
- Some forecasts use default `40/30/30` fallback outputs.
- Team-name handling is fragile for multi-word countries.
- Current "Monte Carlo" wording overstates a deterministic Elo-based projection.
- Preview generation can overwrite curated editorial summaries without an
  operator-facing dry run or diff.

## Ruling

Treat React/Vite + FastAPI as the canonical architecture. Treat Streamlit code
in `src/app/` as legacy/reference unless a later decision restores it.

Open Phase 5: **Framework Rebaseline & Pipeline Hardening**.

Batch 1 is documentation/governance only:

- Rebuild `PROJECT_CHARTER.md` as the current operating contract.
- Update `AGENTS.md` with modern responsibilities for the five framework agents.
- Replace `docs/phase_plan.md` with Phase 5 batches and exit criteria.
- Rebuild `TASKS.md` around the real current deficiencies.
- Add a current `STATUS.md` entry.
- Refresh `docs/DEVELOPER_PLAYBOOK.md`.
- Refresh `README.md` and `docs/domain/README.md` so entrypoint docs do not
  contradict the rebaseline.

## Rationale

The project is not blocked because the app is absent; it is blocked because
ownership, contracts, validation, and deployment truth are no longer aligned.
Continuing to patch code without rebaselining the operating framework would make
the project harder to maintain and harder to delegate.

The Orchestrator needs a current charter and task plan before delegating work to
Data Pipeline, Football Data Scientist, Frontend, and QA roles.

## Consequences

- New feature work should wait until Phase 5 starts with the data contract audit.
- The next queued task is T-024: Data Contract Audit for Active JSON and API
  Payloads.
- `generate_match_previews.py` should not be run again as an overwrite operation
  until dry-run/diff/preserve rules are planned.
- UI/model wording must be reviewed for source-provenance accuracy.
- Deployment docs must distinguish local verification, Cloud Run state, and
  `accionar.xyz` state.

## Verification

Batch 1 changes are documentation-only. Local runtime behavior is unchanged.

Expected local verification after docs update:

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
```

These checks prove that the docs-only rebaseline did not break local Python
syntax or the frontend build. They do not verify BigQuery, Cloud Run, or
`accionar.xyz`.
