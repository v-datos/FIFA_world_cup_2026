# Decision: Decoupled React Client & FastAPI REST Backend Migration

Date: 2026-06-16
Authority: Orchestrator
Status: Decided

## Context

The legacy Streamlit dashboard was layout-restricted, had slow page transitions, and lacked client-side interactivity for player positions, win probability shift charts, and metrics radar. The user approved migrating the app to a custom single-page client built with Vite, React, TypeScript, and TailwindCSS, backed by a FastAPI REST backend.

## Ruling

Migrate the application from the unified Streamlit architecture to a decoupled React Vite frontend and FastAPI backend. Build custom interactive Recharts charts and a coordinate-based squad lineups pitch. Wrap all text in an English/Spanish translation manager. Configure the project using a multi-stage Docker build to serve both the REST API and the React compiled static bundle from a single port, and set up relative base paths for subfolder portability on static hosting.

## Rationale

- **Performance**: Decoupling calculations from rendering gives instantaneous client transitions and high-performance interactive animations.
- **Rich Aesthetics**: Replacing basic Streamlit elements with TailwindCSS v4 and Google Fonts (`Outfit`) allows a high-end glassmorphic dark-mode palette.
- **Interactivity**: Dynamic Recharts Area and Radar charts, plus hover tooltips on a coordinate-based squad pitch, significantly improve tactical engagement.
- **Portability**: Relative asset pathing allows the compiled client files to run seamlessly both inside the FastAPI container and directly hosted on the user's `accionar.xyz/dashboards/fifa-2026/` Apache web server.

## Implementation Notes

- FastAPI backend entrypoint: `src/api/main.py`
- React frontend root: `src/frontend/`
- Docker build config: `Dockerfile` (multi-stage)
- Local test command: `npm --prefix src/frontend run build && python src/api/main.py`
- Cloud Run deploy config: `cloudbuild.yaml`
