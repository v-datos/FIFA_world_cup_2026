<p align="center">
  <img src="readme_banner.png" width="100%" alt="FIFA World Cup 2026 Analytics Dashboard">
</p>

<h1 align="center">FIFA World Cup 2026 Analytics Dashboard</h1>

An interactive web analytics dashboard for monitoring, forecasting, and reviewing matches in the FIFA World Cup 2026.

The dashboard integrates live tournament APIs, curated per-match preview JSON,
Elo-based forecasting, and historical BigQuery/StatsBomb proxy visualizations
into a responsive React/FastAPI application.

**Live Dashboard:** [https://accionar.xyz/dashboards/fifa-2026/](https://accionar.xyz/dashboards/fifa-2026/)

## Key Features

- **Tournament Board & Painters-Tape Bracket**: Fully interactive knockout stage bracket rendering real-time results directly from the tournament API, alongside live Group Stage standings sorted dynamically by points, goal difference, and goals scored.
- **Match of the Day Tactical Previews**: High-quality pre-researched tactical summaries (headlines, formations, systems, injuries, and 3 match-specific insights) for all active calendar games, eliminating generic fallback placeholders.
- **Mathematical Forecaster**: Dixon-Coles Poisson model using Elo inputs to calculate expected goals ($\lambda_1, \lambda_2$), win/draw probabilities, and top 6 exact scorelines.
- **Tournament Progression Estimates**: Elo-based round progression estimates for Round of 16, Quarterfinals, Semifinals, Final, and Champion. The current implementation is deterministic and is queued for model/provenance review.
- **Squad Style & Metric Comparison**: Visualizes team-by-team tactical KPIs from historical tournaments, player rosters, and club affiliations.
- **Bespoke Visualizations**: Renders historical StatsBomb proxy plots including xG distribution comparisons, passing networks, shot maps, touch heatmaps, and progressive action maps using `mplsoccer`.
- **Spanish Translation Toggle**: Seamless switcher at the top of the Match Analysis panel to translate both static labels and dynamic AI tactical text between English and Español.

## Running Locally

The current app is React/Vite plus FastAPI. Run the frontend and backend in
separate terminals during development:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
npm --prefix src/frontend install

# Terminal 1: run API
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: run frontend
npm --prefix src/frontend run dev
```

Local verification:

```bash
python3 -m compileall -q src && npm --prefix src/frontend run build
```

`src/app/` contains legacy Streamlit reference code. It is not the canonical
runtime unless a future decision restores it.

## Compilation & Pipeline

The static data preview files are compiled using the pipeline script:

```bash
python src/pipeline/generate_match_previews.py
```

Current caution: this script can overwrite curated `summary.json` files.
Baseline previews and last-minute match briefings are now separate concepts.
The planned matchday briefing artifact is
`data/matches/{match_id}/briefing.json`; see
`docs/last_minute_briefing_plan.md` before changing generation behavior.
