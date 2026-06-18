# FIFA World Cup 2026 Frontend

React/Vite client for the FIFA World Cup 2026 analytics dashboard.

## Runtime Shape

- Canonical frontend source lives in `src/frontend/src/`.
- The client talks to the FastAPI backend in `src/api/main.py`.
- Built assets are emitted to `src/frontend/dist/`; the Docker build copies that
  output into `src/api/static/` for the deployed FastAPI app.
- `src/app/` is legacy Streamlit reference code, not the production frontend.

## Main Views

- Overview and fixtures of the day.
- Match Analysis, including tactical baseline summaries, forecast states,
  Squad & Style Comparison, radar metrics, progression estimates, and
  StatsBomb proxy visualizations.
- Tournament standings and bracket board.

## Data Contracts

The frontend consumes these backend routes:

- `/api/schedule`
- `/api/match/{match_id}/summary`
- `/api/match/{match_id}/metrics`
- `/api/standings`
- `/api/visualizations/{match_id}/{viz_type}`

Current frontend rules:

- Overview and Match Analysis default to `/api/schedule` entries with
  `lifecycle: "today"` only. Finished and future fixtures stay out of the
  default day view.
- Team names, flags, and slugs must flow through `src/lib/teamIdentity.ts`,
  backed by `data/reference/team_identity.json`.
- `metrics.data_quality.forecast` controls whether forecast probabilities render
  or show "forecast unavailable."
- `metrics.data_quality.team_metrics` controls missing and partial Squad &
  Style states.
- `metrics.data_quality.radar_metrics` controls radar availability.
- `metrics.data_quality.monte_carlo_projections` controls whether progression
  output is labeled as deterministic estimate or true Monte Carlo.
- `summary.briefing_status` controls baseline-only, stale, blocked, or fresh
  briefing messaging.

## Local Development

Install dependencies:

```bash
npm install
```

Run the Vite dev server:

```bash
npm run dev
```

Verify frontend health:

```bash
npm run lint
npm run build
```

The build may warn about large chunks. That warning is currently accepted; it is
not a T-027/T-028 regression.
