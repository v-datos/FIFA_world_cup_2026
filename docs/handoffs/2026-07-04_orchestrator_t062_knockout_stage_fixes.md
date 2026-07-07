# Handoff - Correct Knockout Stage Metadata, Translation, and Dynamic Top Scorers

Date: 2026-07-07
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

3. **Dynamic Top Scorers Resolution**:
   - Refactored the `/api/standings` route in [main.py](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/api/main.py) to calculate top scorers dynamically in real time from the live schedule database, instead of reading a static curated array from `grid_state.json`.
   - Integrated the player name normalization mapping (which merges `K. Mbappé` and `Kylian Mbappé`) and the Game 89 scorer override (assigning Mbappé's penalty goal) directly into the API layer.
   - This ensures the top scorers leaderboard on the dashboard is always up to date and correct in real-time, independent of any network runner IP blockages.

4. **Reference Cache Update**:
   - Synced [games_cache.json](file:///Users/micra/Dataland/FIFA_world_cup_2026/data/reference/games_cache.json) with the latest live matches (bringing Game 93 and 94 results into the local fallback database).

## Verification

- **Syntax & Build**: `python3 -m compileall -q src` and `npm --prefix src/frontend run build` succeed with zero errors.
- **Local Testing**: Standings API endpoint returns correct dynamic top scorers list (Haaland, Mbappé, Messi at 7 goals). Match Analysis and Overview tabs show correct stage names and top scorer list in both languages.
