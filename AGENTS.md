# AGENTS.md — Operating Document for FIFA World Cup 2026 Dashboard

**Status:** Living document. Edit the "Shared Conventions" section first when changing anything global — every agent below references it.

---

## Table of contents

1. [Orchestrator](#1-orchestrator)
2. [Football Data Scientist](#2-domain-expert)
3. [Data Pipeline Engineer](#3-data-engineer)
4. [Frontend Engineer](#4-analyst)
5. [QA / Reproducibility Engineer](#5-qa--reproducibility-engineer)

---

## Shared conventions

Every agent operates within these rules. Violations are escalated to the Orchestrator.

**Repository layout** — the tree below is the **software-app** profile's:

```
data/
  matches/                   # Pre-calculated static JSON files
src/
  analytics/                 # BigQuery metrics and visualization generators
  app/                       # Streamlit frontend app
  pipeline/                  # Data compilation scripts
docs/                        # Planning, decisions, handoffs, contracts
```

**Canonical processed artifacts**:
- `data/matches/{match_id}/metrics.json` — Aggregated match statistics and visual timelines.
- `data/bracket/grid_state.json` — Bracket configurations.

**Keys & types:** Python dicts/lists mapped to JSON.

**Tooling:** Python, Streamlit, google-cloud-bigquery, mplsoccer, pandas.

**Code style:** PEP8, clear docstrings, typing where appropriate.

**Reproducibility contract:** Every output is regenerable from the project's **verify command** (`python compile_static_fixtures.py --dry-run`).

---

## 1. Orchestrator
Manages the workflow, delegates to other agents, updates TASKS.md.

---

## 2. Football Data Scientist
Defines the metrics, expected data output, tactical views, and ensures the AI Studio NLP summaries match real football reality.

---

## 3. Data Pipeline Engineer
Builds the `compile_static_fixtures.py` script and connects BigQuery to local static JSON payloads.

---

## 4. Frontend Engineer
Builds the Streamlit UI, custom CSS injections for the painter's tape brackets, and wires the frontend to the static JSON files.

---

## 5. QA / Reproducibility Engineer
Validates Python scripts, ensures JSON outputs are correct, and tests the Streamlit application.

---

## Handoff-contract summary (quick reference)

| From → To | Artifact | When |
|---|---|---|
| Data Pipeline Engineer → Frontend Engineer | Local static JSON metrics | Post-compilation |
| All agents → QA / Reproducibility | Code + outputs at phase boundary | Phase boundaries |
