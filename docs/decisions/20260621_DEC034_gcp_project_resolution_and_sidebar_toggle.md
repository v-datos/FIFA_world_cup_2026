# DEC034 - GCP Project Resolution & Sidebar Toggle Placement

Date: 2026-06-21

## Status

Accepted.

## Context

During Spanish translation testing on the deployed Cloud Run instance, the backend returned HTTP 200 but left the content in English. Investigation of the logs revealed a `403 PERMISSION_DENIED` exception from Vertex AI:
`Permission 'aiplatform.endpoints.predict' denied on resource '//aiplatform.googleapis.com/projects/statsbomb-db/locations/us-central1/publishers/google/models/gemini-2.5-flash'`

This occurred because the codebase defaulted to a legacy developer project ID (`statsbomb-db`) if `GEMINI_PROJECT` was unset. On Cloud Run, the service runs under the project `midyear-castle-328020` where the service account actually has Vertex AI permissions.

Additionally, the EN/ES toggle was positioned fixed in the top-right corner of the page, cluttering the main content header. The user requested moving it into the navigation sidebar directly below 'Tabla y Llaves' ('Standings & Bracket').

## Decision

- **Dynamic Project ID Resolution**: Updated `src/api/main.py`, `src/pipeline/generate_match_headlines.py`, and `src/pipeline/generate_team_news.py` to resolve the GCP project dynamically in this order:
  1. `GEMINI_PROJECT` (env variable)
  2. `GOOGLE_CLOUD_PROJECT` (env variable automatically set by Cloud Run)
  3. `"midyear-castle-328020"` (fallback to the project housing the repository resources)
- **Sidebar Toggle Relocation**: Relocated the language toggle from `App.tsx` into `components/Sidebar.tsx` directly below the navigation links. Added responsive layout rules:
  - **Expanded state**: Renders a clear, labeled, horizontal layout.
  - **Collapsed state**: Renders a compact, single-button language switcher button displaying the alternative language (e.g. `ES` or `EN`) to save space.

## Consequences

- Full translation functionality successfully restored on Cloud Run, eliminating English text fallbacks in Spanish mode.
- Improved header aesthetics by cleaning up the top-right layout.
- Consistent language toggle experience across different sidebar widths.
