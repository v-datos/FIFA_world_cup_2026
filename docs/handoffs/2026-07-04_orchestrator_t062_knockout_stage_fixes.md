# Handoff - Correct Knockout Stage Metadata and Translation

Date: 2026-07-04
Task: T-062
Status: Completed
Owner: Orchestrator / Frontend Engineer / Data Pipeline Engineer

## Deliverables

1. **Knockout Stage Sourcing (T-062)**:
   - Fixed `_create_fixture_folder` and `write_caches` in [collect_espn_matchday.py](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/pipeline/collect_espn_matchday.py) which was incorrectly hardcoding knockout games to `"Group Stage"` if the team was in `group_map`.
   - Integrated live simulation database lookup to resolve the correct tournament stage (`type` and `group` fields) from `fetch_live_games_for_schedule`.

2. **Match Stage Translation**:
   - Created a `translateStage` helper function in [translations.ts](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/frontend/src/lib/translations.ts) that maps English stage names to their Spanish equivalents (e.g. `Group Stage - Group B` -> `Fase de grupos - Grupo B`, `Round of 32` -> `Dieciseisavos de final`, `Round of 16` -> `Octavos de final`, `Quarterfinal` -> `Cuartos de final`, etc.).
   - Integrated `translateStage` into [MatchAnalysisTab.tsx](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/frontend/src/components/MatchAnalysisTab.tsx) and [OverviewTab.tsx](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/frontend/src/components/OverviewTab.tsx).

3. **Existing Data Remediation**:
   - Created and executed a one-off correction script `scratch/fix_stages.py` that scanned existing `summary.json` files on disk and updated wrong stage headers to matching simulation database values (`brazil_japan_2026`, `germany_paraguay_2026`, `netherlands_morocco_2026`, `south_africa_canada_2026` corrected to `Round of 32`).

## Verification

- **Syntax & Build**: `python3 -m compileall -q src` and `npm --prefix src/frontend run build` succeed with zero errors.
- **Local Testing**: Match Analysis and Overview tabs show correct stage names in both Spanish and English.
