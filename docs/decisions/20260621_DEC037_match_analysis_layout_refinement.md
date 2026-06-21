# DEC037 - Match Analysis Layout Refinement

Date: 2026-06-21

## Status

Accepted.

## Context

The Match Analysis tab had separate columns for Match Outcome Probability (Dixon-Coles predictions) and Monte Carlo Tournament Projections. Additionally, the Key Insights, Injuries, and Last Standing details were squished inside a grid beside the Outcome Probability graph.

To optimize visual hierarchy and utilize horizontal screen space better:
1. The Key Insights, Injuries, and Last Major Standing card should be full-width, located directly below the AI Tactical Headline.
2. The Dixon-Coles prediction information (Match Outcome Probability, Top Exact Scores) and the Monte Carlo Projections should be merged into a single card and placed directly under the Performance Radar comparison card in the left column.

## Decision

- **Key Insights Relocation**: Moved the Key Insights, Injuries, and Last Major Standing card outside of the grid, placing it directly below the AI Tactical Headline card so that it spans the full viewport width.
- **Three-Column Inner Layout**: Refactored the internal layout of the insights card to utilize a responsive 3-column layout (`grid grid-cols-1 md:grid-cols-3`) with border dividers on desktop, preventing horizontal stretching.
- **Monte Carlo & Outcome Probability Card Merge**: 
  - Added a `noWrapper` option to the `MonteCarloProjections` component to support rendering its contents inside other cards without duplicating the card container styling.
  - Imported and embedded `MonteCarloProjections` directly inside the `MatchPredictionGraph` component, separated by a visual divider line.
  - Placed the combined graph card directly underneath `TeamRadarComparison` inside the left column of the grid layout.
- **Clean Unused Imports**: Removed the unused `MonteCarloProjections` import from `MatchAnalysisTab.tsx`.

## Consequences

- Improved layout hierarchy: all textual qualitative analysis (headline, insights, injuries, standing) is consolidated at the top in full-width, scannable blocks.
- Compact quantitative projection center: predictions, exact scores, and tournament progression simulations are merged into a single card below the team performance metrics radar.
- Full build and TypeScript compliance verified.
