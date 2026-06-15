# Handoff: Orchestrator - 2026-06-15

## What was produced

- Dynamic standings update pipeline (`update_live_standings.py`) with correct group sorting tiebreakers.
- Live API-driven knockout bracket mapping (`bracket_ui.py`) linked to the `/get/games` schedule.
- Automated AI match preview generator (`generate_match_previews.py`) integrated with BigQuery metrics and Gemini on Vertex AI.
- Streamlit application modifications to dynamically load previews from file folders (`app.py`).
- Cloud Run container rebuild and deployment.
- Deployed website integration routing under `https://accionar.xyz/dashboards/fifa-2026/`.

## Known limitations

- Gemini API Vertex AI access throws 404 in some locations for specific model configurations; a mock generator fallback is implemented to handle service rate limits/access errors gracefully.

## Next steps

- Implement database storage sync (Phase 3) connecting local standings to the PostgreSQL NestJS server once credentials/server endpoints are deployed.
