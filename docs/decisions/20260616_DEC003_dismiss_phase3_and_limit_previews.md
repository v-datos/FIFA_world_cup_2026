# Decision: Dismiss Phase 3 Standings Ingestion & Restrict Match Previews to Active Day

Date: 2026-06-16
Authority: Orchestrator
Status: Decided

## Context

1. **Phase 3 Standings Ingestion**: The project charter originally included Phase 3 to connect local group standings to a live Nestor PostgreSQL/NestJS backend server database once deployed.
2. **Match Previews Dropdown Clutter**: The Match Analysis tab contains previews for all upcoming matches (spread across multiple days), which cluttered the selectbox dropdown. Additionally, the user requested showing only "games of the day" and using the latest pre-match preview information.

## Ruling

1. **Dismiss Phase 3**: Cancel all planned backend integration work for Standings Ingestion Sync. The current direct API polling of `https://worldcup26.ir` combined with local static fallback (`grid_state.json`) is fully sufficient. No external database credentials or setups are needed.
2. **Restrict Previews Dropdown**: Modify `src/app/app.py` to dynamically filter the "Select 2026 Fixture Preview" dropdown list to show *only* the matches of the current active date (defined as the date of the next upcoming/unfinished match in the schedule).

## Rationale

- Dismissing Phase 3 prevents unnecessary infrastructure dependencies, reduces maintenance overhead, and respects the user's preference to keep the application lightweight and cost-effective.
- Restricting the dropdown to the active date removes clutter, keeping the focus entirely on the match of the day.
- Dynamically computing the active date from the next unfinished match ensures the dropdown updates itself automatically as the tournament progresses from day to day, without manual configuration.

## Implementation Notes

- **App Code**: Updated [src/app/app.py](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/app/app.py) to parse date/time strings from match summaries, find the active match date based on current time (with a 2.5-hour buffer for active matches), and filter the selectbox options.
- **Documentation**: Updated [PROJECT_CHARTER.md](file:///Users/micra/Dataland/FIFA_world_cup_2026/PROJECT_CHARTER.md), [STATUS.md](file:///Users/micra/Dataland/FIFA_world_cup_2026/STATUS.md), [TASKS.md](file:///Users/micra/Dataland/FIFA_world_cup_2026/TASKS.md), and [docs/phase_plan.md](file:///Users/micra/Dataland/FIFA_world_cup_2026/docs/phase_plan.md) to record this decision and mark the project as complete.
