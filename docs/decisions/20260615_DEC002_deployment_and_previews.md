# Decision: Standings Corrections, Dynamic Bracket, and Previews Automation

Date: 2026-06-15
Authority: Orchestrator
Status: Decided

## Context

The Tournament Board tab displayed incorrect group standings (e.g., Brazil having 3 points instead of 1) due to incorrect sorting and dictionary-wrapped groups response from the API. Additionally, match previews for upcoming games were hardcoded and required manually generated Vertex AI summaries.

## Ruling

Implement automated standing sorting tiebreakers, dynamic bracket mapping to the live `/get/games` API, and an automated Vertex AI/BigQuery upcoming match preview generation pipeline. Rebuild the container and deploy to Cloud Run, and integrate the dashboard iframe route in the personal website portfolio.

## Rationale

- Automating the standings sorting tiebreakers (Points -> Goal Difference -> Goals For) ensures correct standings representation.
- Mapping the games API dynamically allows the knockout bracket to update in real-time as games complete.
- Dynamic file-based previews avoid hardcoded selectors and enable the preview generator to run as a cron pipeline.

## Implementation Notes

- Live standings update script: `src/pipeline/update_live_standings.py`
- Symmetrical bracket view script: `src/app/bracket_ui.py`
- Match preview generator script: `src/pipeline/generate_match_previews.py`
- Personal website integration repository: `web_accionar_xyz`
- Cloud Run URL: `https://fifa-2026-dashboard-80399171028.us-central1.run.app`
- Portfolio URL: `https://accionar.xyz/dashboards/fifa-2026/`
