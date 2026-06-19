# Project Context: FIFA World Cup 2026 Analytical Dashboard

Status: Initial setup context. This file is retained as background only and is
not the current architecture source of truth. For current runtime, data
contracts, and task routing, use `PROJECT_CHARTER.md`, `TASKS.md`, `STATUS.md`,
`docs/phase_plan.md`, and `docs/data_contracts.md`.

## 1. Overview & Objective
The goal is to build a high-performance web application tracking the live FIFA World Cup 2026. The application filters out media noise by combining advanced data science metrics with programmatic NLP news summaries. It serves a small, targeted user base (friends and family).

## 2. Core Frontend Layout Requirement
The user interface is restricted to 3 clean sections:
* **Section 1: The Lo-Fi Brackets Grid:** A digital reproduction of a tactical tournament wall chart. It must mimic a physical board made with painters' tape and permanent markers.
* **Section 2: Group Standings & Basic Stats:** High-level tables highlighting live points, goal differentials, and underlying metrics ($xG$, field tilt).
* **Section 3: Match of the Day Analytics Panel:** An interactive preview module triggered by clicking on a daily fixture. It splits into three layers:
    1. AI Narrative Summary (Isolating injuries, confirmed tactics, and facts; stripping out fluff).
    2. Probabilistic Prediction (Calculated using Poisson/Dixon-Coles match simulation models).
    3. Bespoke Tactical Visualizations (Passing networks, shot maps, radar charts, and xG timelines).

## 3. Existing Local Codebase Assets
The project inherits an existing, production-grade codebase connected to a Google Cloud BigQuery backend storing StatsBomb event data:
* `fifa_dashboard_3.py`: Main Streamlit application file defining tab routes and styling options.
* `fifa_metrics_bq.py`: Data aggregation layer containing single-pass CTE queries (e.g., `get_match_stats_both_teams`, PPDA, field tilt, and actions under pressure).
* `fifa_visualizations_bq.py`: Rendering engine utilizing `mplsoccer`, Plotly, and Matplotlib for pitch maps, match momentum graphs, and radar charts.
* `Metrics.md`: Comprehensive data sheet documenting all metric definitions and SQL aggregation logic.
