# STATUS

## 2026-06-16 - Vite + React Client & FastAPI Decoupled Migration Completed

Prepared by: Orchestrator

### Current Objective

Migrate the dashboard from Streamlit to a decoupled architecture consisting of a FastAPI REST backend and a modern React client built with Vite and TailwindCSS, incorporating interactive vector charts and a dynamic lineup pitch.

### Completed This Update

- **REST API Backend**: Created `/src/api/main.py` using FastAPI, exposing REST endpoints for schedule, match summary, metrics, live standings, and dynamic StatsBomb matplotlib base64 visualizations.
- **Root Asset Serving**: Integrated FastAPI's `StaticFiles` mount at `/` to serve the compiled frontend single-page application directly from the unified python container.
- **Vite React Client**: Initialized client under `/src/frontend/` using Vite, React 19, TypeScript, and TailwindCSS v4.
- **Interactive Pitch Lineup**: Implemented the HTML5/CSS canvas pitch model in `InteractivePitch.tsx` that dynamically maps players based on formation (`4-3-3`, `4-1-4-1`, `3-5-2`) and displays player metadata and entity crosswalk IDs on hover.
- **Animated Charting**: Wired win probability shift curves and team radar comparisons utilizing interactive, responsive vector SVG components via **Recharts**.
- **Live standings & Bracket**: Built the live tournament center (`StandingsTab.tsx`) rendering standings for all 12 groups (A to L) and the live knockout tree (Round of 32 to Final).
- **Static Base Portability**: Set `base: './'` in Vite config to ensure compiled static bundles can be hosted seamlessly in a subfolder on `accionar.xyz/dashboards/fifa-2026/` or at the root path on Cloud Run.

### Next Sprint Priorities

- Verify Cloud Run deployment.
- Upload compiled React static assets to `accionar.xyz` folder structure.

---

## 2026-06-15 - Match Analysis Tab Bug Fixes & Previews Resiliency Completed

Prepared by: Orchestrator

### Current Objective

Ensure correct group standings sorting, dynamic knockout bracket updates from API, and fully automated, resilient match previews and tactical comparisons without crashes or empty views on the dashboard.

### Completed This Update

- **Standings Parsing & Sorting**: Corrected the parsing of groups from the API and sorted standings descending by points (`pts`), then goal difference (`gd`), then goals for (`gf`).
- **Dynamic API-Driven Bracket**: Configured bracket rounds mapping to the live `/get/games` schedule. Bracket advances teams and scores automatically in real time.
- **AI Match Previews & Resiliency**: Resolved the `KeyError: 'team_metrics'` crash in the Streamlit app. Configured the generation pipeline to write the `team_metrics` block containing ELO and FBref statistics for both teams.
- **New Team Profiles & Rosters**: Populated static rosters, club affiliations, and tournament standings for 8 new teams (Spain, Cape Verde, Belgium, Egypt, Saudi Arabia, Uruguay, Iran, New Zealand) and handled spelling normalization for Côte d'Ivoire.
- **Expanded upcoming games coverage**: Increased upcoming preview limits from 3 to 8 matches, resolving the missing **Iran vs New Zealand** fixture on June 15, 2026.
- **Cloud Run Deployment**: Rebuilt the Docker container and redeployed the live dashboard.
- **Tournament Board Standing Update Fix**: Installed `curl` inside the slim Docker container image to resolve the silent failure of runtime standings API calls, and updated the local `grid_state.json` fallback.
- **Portfolio Website Integration**: Synchronized the React routing changes and whitelisted the CSP `frame-src` in `.htaccess` on the remote server via SSH.
