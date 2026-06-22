# DEC038 - Match Analysis 70/30 Insights & Radar Layout

Date: 2026-06-22

## Status

Accepted.

## Context

Following the consolidation of textual insights and quantitative projections, the Key Insights card spanned the full width of the viewport, which created excessive empty space on wider desktop monitors. Additionally, the Performance Radar comparison card was located in the lower grid block, separate from the primary match data summary at the top.

To improve visual balance and compact the dashboard layout on desktop screens, the Key Insights card and the Performance Radar card should be brought into a single row, allocating 70% of the row width to Key Insights and 30% to the Radar card.

## Decision

- **Grid Alignment**: Reorganized [MatchAnalysisTab.tsx](file:///Users/micra/Dataland/FIFA_world_cup_2026/src/frontend/src/components/MatchAnalysisTab.tsx) to place the Key Insights card and the `TeamRadarComparison` card in a single grid row using a 10-column grid container (`grid grid-cols-1 lg:grid-cols-10`).
- **Width Splits**:
  - Key Insights card: assigned `lg:col-span-7` (70% width on desktop).
  - Radar card: wrapped in a container with `lg:col-span-3` (30% width on desktop) and `flex flex-col h-full` to match height.
  - Below them, the Match Outcome/Monte Carlo prediction card (`MatchPredictionGraph`) and the squad styles comparison card (`SquadStyleComparison`) remain side-by-side in a 50/50 split (`grid-cols-1 lg:grid-cols-2`).
- **Mobile Stacking**: Confirmed that the layout degrades gracefully to stacked columns on mobile screens (`grid-cols-1`).

## Consequences

- Highly efficient screen space utilization: qualitative insights and basic radar metrics are grouped together near the top of the dashboard.
- The 3-column inner layout of the Insights card remains readable and acts as a grid on desktop, stacking cleanly on smaller viewports.
- All code compilation and static asset builds successfully verified.
