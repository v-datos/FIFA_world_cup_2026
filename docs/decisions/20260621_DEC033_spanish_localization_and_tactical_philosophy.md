# DEC033 - Spanish Localization & Automated Tactical Philosophy Generation

Date: 2026-06-21

## Status

Accepted.

## Context

The Match Analysis tab supported a Spanish translation toggle on the frontend, but the backend returned headlines, tactical insights, and team philosophies in English only. This caused mixed-language layouts when Spanish was selected. Additionally, the squad lineups section displayed a generic placeholder phrase ("Confirmed XI from ESPN match data.") for tactical philosophy when actual tactical system details were not pre-calculated or stored in the cache.

To provide a fully premium, immersive bilingual experience, we needed to dynamically localize the tactical editorial content and replace generic team philosophy placeholders with real, web-grounded tactical setup descriptions.

## Decision

- **Bilingual API Content Support**: Updated the `/api/match/{match_id}/summary` endpoint to accept a `lang` parameter. When set to `es` or `Español`, the backend leverages Gemini to translate the key headline, tactical insights, and team philosophies into natural, professional Spanish using football-specific terminology.
- **Disk Caching for Translations**: Translated payloads are cached locally as `data/matches/{match_id}/summary_es.json` alongside their English counterparts. Subsequent requests load from the disk cache if the translation timestamp matches the current English headline timestamp, preventing redundant LLM API calls and conserving quota.
- **Automated Web-Grounded Tactical Philosophy**: Added a fallback generator in the lineups data pipeline. If a team's tactical philosophy in the cache is generic (e.g., "Confirmed XI from ESPN match data.", "None", etc.), the system dynamically queries Gemini using the Google Search grounding tool to research and write a punchy, 20-word description of the team's system/manager setup. The generated philosophy is written back to the lineups cache `data/source_cache/lineups/latest.json` for persistence.
- **Frontend Alignment**: Refactored frontend components (`MatchAnalysisTab.tsx`, `BriefingFreshnessBadge.tsx`, `MatchPredictionGraph.tsx`, etc.) to pass the active language to the backend and handle Spanish outcomes correctly.

## Consequences

- Full translation coverage of Match Analysis, eliminating mixed English-Spanish layouts.
- Tactical philosophies are dynamically and automatically researched from the web when missing or generic, enriching the team profiles on the lineup pitch.
- Translation caching ensures low-latency responses and minimizes Vertex AI cost.
- Lineup cache `data/source_cache/lineups/latest.json` is updated in-place with real-world descriptions.
