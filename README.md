<p align="center">
  <img src="readme_banner.png" width="100%" alt="FIFA World Cup 2026 Analytics Dashboard">
</p>

<h1 align="center">FIFA World Cup 2026 Analytics Dashboard</h1>

An interactive web analytics dashboard for monitoring, forecasting, and reviewing matches in the FIFA World Cup 2026.

The dashboard integrates real-time schedule APIs, BigQuery historical match datasets, and advanced predictive algorithms (such as the Dixon-Coles Poisson forecasting model and Monte Carlo simulation projections) into a premium, responsive dark-themed UI.

**Live Dashboard:** [https://accionar.xyz/dashboards/fifa-2026/](https://accionar.xyz/dashboards/fifa-2026/)

## Key Features

- **Tournament Board & Painters-Tape Bracket**: Fully interactive knockout stage bracket rendering real-time results directly from the tournament API, alongside live Group Stage standings sorted dynamically by points, goal difference, and goals scored.
- **Match of the Day Tactical Previews**: High-quality pre-researched tactical summaries (headlines, formations, systems, injuries, and 3 match-specific insights) for all active calendar games, eliminating generic fallback placeholders.
- **Mathematical Forecaster**: A dynamic implementation of the Dixon-Coles Poisson model to calculate expected goals ($\lambda_1, \lambda_2$), win/draw probabilities, and top 6 exact scorelines.
- **Monte Carlo Projections**: Simulates 10,000 tournament pathways based on team Elo ratings to estimate round progression probabilities (Round of 16, Quarterfinals, Semifinals, Final, and Champion).
- **Squad Style & Metric Comparison**: Visualizes team-by-team tactical KPIs from historical tournaments, player rosters, and club affiliations.
- **Bespoke Visualizations**: Renders StatsBomb event-level plots including xG Momentum timelines, passing networks, shot maps, and player touch heatmaps using `mplsoccer` proxy mapping.
- **Spanish Translation Toggle**: Seamless switcher at the top of the Match Analysis panel to translate both static labels and dynamic AI tactical text between English and Español.

## Running Locally

To run the dashboard locally, make sure you have python installed, and run:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run src/app/app.py
```

## Compilation & Pipeline

The static data preview files are compiled using the pipeline script:

```bash
python src/pipeline/generate_match_previews.py
```

This updates match preview details under `data/matches/` with schedule information and statistical comparisons.
