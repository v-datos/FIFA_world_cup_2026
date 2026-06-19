# Handoff - T-041 Documentation Clutter Audit

Date: 2026-06-19
From: Orchestrator
To: Orchestrator, QA / Reproducibility Engineer, all implementation agents
Status: Complete

## Summary

T-041 reviewed the documentation set after T-039 and separated current-state
documents from historical records. No documentation files were deleted.

The main output is:

- `docs/documentation_clutter_audit.md`
- `docs/decisions/20260619_DEC018_documentation_clutter_map.md`

## What Changed

- Updated `README.md` to describe active seeded Monte Carlo and the World
  Football Elo rating cache.
- Updated `docs/DEVELOPER_PLAYBOOK.md` to remove stale deterministic-projection
  and multi-word parsing caveats.
- Updated `docs/data_contracts.md` next-step routing to T-038/T-033/T-029.
- Marked `PROJECT_CONTEXT.md` as initial setup context only.
- Updated `PROJECT_CHARTER.md` with recent decisions, source-cache architecture,
  and the documentation-clutter risk.
- Added the current documentation reading order and retention classes.

## Current Documentation Rule

Use current-facing docs first:

1. `PROJECT_CHARTER.md`
2. `AGENTS.md`
3. `TASKS.md`
4. `STATUS.md`
5. `docs/phase_plan.md`
6. `docs/data_contracts.md`
7. `docs/model_provenance.md`
8. `docs/DEVELOPER_PLAYBOOK.md`

Decision and handoff files remain historical. They may contain superseded facts
that were true at the time of completion.

## Remaining Documentation Risks

- `STATUS.md` is large but still useful as newest-first chronology. Archive only
  if navigation becomes a real blocker.
- T-029 still needs the deployment/operations runbook refresh.
- T-030 still needs the Streamlit legacy disposition decision.

## Next Step

Proceed to T-038 - Source-Backed Squad & Style Metrics Integration.

## Verification

- `git diff --check`
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
