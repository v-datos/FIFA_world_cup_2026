# Local Implementation Roadmap

## Phase 1: Environment Setup & Codebase Consolidation
* [ ] Initialize the local repository environment on the desktop app.
* [ ] Verify Python dependencies matching your core data tools (`streamlit`, `pandas`, `google-cloud-bigquery`, `plotly`, `mplsoccer`).
* [ ] Map directory paths to easily reference the shared logic from your existing dashboard instances (`/dashboards/matches/` and `/dashboards/competitions/`).

## Phase 2: Building the Section 1 CSS Grid Component
* [ ] Write a custom style module (`style_whiteboard.py`) containing the structural classes needed to render the painters-tape borders.
* [ ] Integrate Google Web Fonts within the Streamlit initialization script to import the handwritten text style.
* [ ] Build mock structural matrices to verify layout scaling on both web browsers and mobile screens.

## Phase 3: AI Studio Prompt Sandboxing & Antigravity Ingestion Loop
* [ ] Set up prompt parameters within Google AI Studio to accurately isolate squad tracking data.
* [ ] Wrap the generation script within an Antigravity background task context manager to periodically write outputs to local JSON files.
* [ ] Merge the static text summaries with live win/loss probability predictions.

## Phase 4: Integration of `fifa_metrics_bq.py` and `fifa_visualizations_bq.py`
* [ ] Wire Section 3 match selection clicks to your existing BigQuery data structures.
* [ ] Test loading speeds for unified match data calls to minimize query execution overhead.
* [ ] Add reactive toggle switches allowing users to flip between team pitch pass maps, touch heatmaps, and defensive coverage diagrams.