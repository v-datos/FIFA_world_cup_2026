# Handoff - Correct Knockout Stage Metadata and Translation

Date: 2026-07-06
Task: T-062
Status: Completed
Owner: Orchestrator / Frontend Engineer / Data Pipeline Engineer

## Deliverables

1. **Knockout Stage Sourcing (T-062)**:
   - Fixed `_create_fixture_folder` and `write_caches` in [collect_espn_matchday.py](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/pipeline/collect_espn_matchday.py) which was incorrectly hardcoding knockout games to `"Group Stage"` if the team was in `group_map`.
   - Integrated live simulation database lookup to resolve the correct tournament stage (`type` and `group` fields).
   - Removed imports from `src.api.main` inside `collect_espn_matchday.py` by implementing a standalone `_load_live_game_index()` helper. This prevents `ModuleNotFoundError` crashes in minimal CI environments (like the automated GitHub Actions runner) where `fastapi`, `pandas`, and other heavy API dependencies are not installed.

2. **Match Stage Translation**:
   - Created a `translateStage` helper function in [translations.ts](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/frontend/src/lib/translations.ts) that maps English stage names to their Spanish equivalents (e.g. `Group Stage - Group B` -> `Fase de grupos - Grupo B`, `Round of 32` -> `Dieciseisavos de final`, `Round of 16` -> `Octavos de final`, `Quarterfinal` -> `Cuartos de final`, etc.).
   - Integrated `translateStage` into [MatchAnalysisTab.tsx](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/frontend/src/components/MatchAnalysisTab.tsx) and [OverviewTab.tsx](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/frontend/src/components/OverviewTab.tsx).

3. **Existing Data Remediation**:
   - Hardened `data/reference/games_cache.json` to store all 104 matches, acting as a complete fallback.
   - Remediated stage labels on disk for all incorrect group-stage guesses generated during bot refresh runs (including `portugal_spain_2026` and `united_states_belgium_2026` to `Round of 16`).

## Verification

- **Syntax & Build**: `python3 -m compileall -q src` and `npm --prefix src/frontend run build` succeed with zero errors.
- **Local Testing**: Match Analysis and Overview tabs show correct stage names in both Spanish and English.
