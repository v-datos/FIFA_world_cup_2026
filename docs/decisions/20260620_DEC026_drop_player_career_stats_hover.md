# DEC026 - Drop Player Career-Stats Hover Endpoint (T-019)

Date: 2026-06-20

## Status

Approved.

## Context

Task `T-019 - Player Career-Stats Hover Endpoint` was queued/deferred in the backlog. It proposed building an `/api/player/stats` route backed by a BigQuery historical dataset to show career statistics in the lineup pitch tooltips. 

However, a review of the current React/Vite dashboard implementation (`InteractivePitch.tsx`) reveals that:
1. The frontend pitch tooltips only render the player's Name, Position, and Club (resolved via data pipeline lineups cache).
2. The frontend does not make any requests to a player stats endpoint and does not have UI layout slots to present career statistics.
3. Querying career stats from historical BigQuery tables is complex, credential-dependent, and goes against the project's goal of serving fresh, online/AI-researched tournament analysis.

## Decision

- **Drop Task T-019**: Remove `T-019` from the project backlog entirely.
- **Retain Clean Lineups Presentation**: Keep the lineup pitch tooltip simple, rendering only the player's Name, Position, and Club as currently implemented.
- **Maintain No-Dependency Dev Experience**: Prevent adding complex Google Cloud BigQuery credential dependencies for local execution/development.

## Consequences

- The project backlog is simplified.
- Codebase remains clean and free of dead or unused backend endpoints.
- No local configuration changes or BigQuery IAM permissions are required for developers.
