# DEC032 - Grounded Web Search for AI Tactical Previews (Headlines + Insights)

Date: 2026-06-21

## Status

Accepted.

## Context

The match preview pipeline (`generate_match_headlines.py`) was generating tactical headlines and insights solely based on local structured metrics (Elo ratings, win probabilities, average possession/shots).
While functional, this approach missed late-breaking squad news, tactical shifts, and real-time manager/player updates that cannot be captured by static historical statistics alone.

Additionally, the script was using the legacy `vertexai` SDK, which triggered deprecation warnings for removal in June 2026.

## Decision

- **Migrate to modern `google-genai` SDK:** Fully migrate the script to use the modern `google-genai` client libraries, aligning with the project's standard AI stack.
- **Implement Grounded Web Search:** Implement a two-step prompt sequence:
  1. Use the `google_search` tool to execute a web-grounded search query for tactical updates, projected formations, news, and manager statements on the two competing teams.
  2. Parse the search report alongside the local numerical style metrics/Elo values into a structured JSON payload containing a tactical headline (under 12 words) and exactly three insights.
- **Support Graceful Fallback:** If the web search grounding fails or is blocked, fall back gracefully to local numerical style metrics/Elo only, setting `"headline_source": "ai_generated"` instead of `"ai_web_grounded"`.

## Consequences

- Match headlines and insights now reflect real-time squad news and web-grounded tactical facts.
- Legacy `vertexai` deprecation warnings are resolved.
- Robust execution in GHA workflows with fallback protection.
