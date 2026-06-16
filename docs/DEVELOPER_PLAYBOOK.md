# Developer Playbook & Standard Operating Procedure (SOP)
## FIFA World Cup 2026 Dashboard & Accionar Integration

This document outlines the architecture, data structures, deployment workflows, and common troubleshooting steps for the FIFA World Cup 2026 Dashboard and its integration into `https://accionar.xyz`.

---

## 1. System Architecture

The project consists of two distinct components:
1. **FIFA World Cup 2026 Dashboard (Streamlit App):**
   * **Local Path:** `/Users/micra/Dataland/FIFA_world_cup_2026`
   * **Hosting:** Cloud Run (`https://fifa-2026-dashboard-80399171028.us-central1.run.app`)
2. **accionar.xyz Portfolio Website (React + TypeScript + Vite):**
   * **Local Path:** `/Users/micra/Documents/accionar.xyz/web_accionar_xyz`
   * **Hosting:** IONOS Web Hosting (`https://accionar.xyz`)
   * **Integration:** Embeds the Streamlit dashboard via an `<iframe>` in `src/app/index.tsx`.

---

## 2. Key Dashboard Files & Data Flows

### A. Tournament Board (Standings & Bracket)
* **Logic File:** `src/app/bracket_ui.py`
* **Static Fallback:** `data/bracket/grid_state.json`
* **Data Sources:** 
  * Live Standings: `https://worldcup26.ir/get/groups`
  * Live Match Results: `https://worldcup26.ir/get/games`
* **Runtime Sync:** The app executes `curl -s -k` via a subprocess at runtime. If the API request succeeds, it dynamically parses the standings and builds the bracket. If it fails, it falls back to the static `grid_state.json` inside the container image.

### B. Match Analysis (AI Previews & Squad Lists)
* **Logic File:** `src/app/app.py`
* **Preview Generator:** `src/pipeline/generate_match_previews.py`
* **Rosters & Standings Data:** Static dictionaries in `src/app/app.py` (e.g. `ROSTERS_2026`, `LAST_TOURNAMENT_STANDINGS_2026`, `PLAYER_CLUBS_2026`).
* **Match Previews Path:** Pre-generated JSON files in `data/matches/{match_id}/metrics.json` containing ELO, tactical stats, and Gemini AI narratives.

---

## 3. Playbook: Common Tasks & Procedures

### Task 1: Updating Live Match Standings (Local Sync)
To update the local fallback JSON file with the latest match points:
1. Run the update script:
   ```bash
   python scripts/update_live_standings.py
   ```
2. Verify the changes in `data/bracket/grid_state.json`.

### Task 2: Modifying Rosters, Clubs, or Historic Standings
When new teams are introduced or squad lists need changes:
1. Open `src/app/app.py`.
2. Locate the static dictionaries near the top of the file:
   * `ROSTERS_2026` (list of players)
   * `PLAYER_CLUBS_2026` (club teams & Elo ratings)
   * `LAST_TOURNAMENT_STANDINGS_2026` (past World Cup / International results)
3. Modify or append the values accordingly.

### Task 3: Regenerating Match Previews & AI Summaries
To update match previews for upcoming fixtures:
1. Run the preview generation pipeline:
   ```bash
   python src/pipeline/generate_match_previews.py
   ```
2. Ensure the JSON outputs (such as `data/matches/iran_new_zealand_2026/metrics.json`) are correctly generated and contain both Gemini text and the `team_metrics` block.

---

## 4. Deployment Procedures

### Deployment A: Streamlit Dashboard to Cloud Run
1. Navigate to the project root:
   ```bash
   cd /Users/micra/Dataland/FIFA_world_cup_2026
   ```
2. Submit the build to Google Cloud Build (which compiles the Docker container and deploys it):
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```
3. Cloud Run automatically handles the rollout of the new revision.

### Deployment B: Rebuilding & Uploading the accionar.xyz Website
If you update the website's iframe route or CSP whitelist:
1. Navigate to the website root:
   ```bash
   cd /Users/micra/Documents/accionar.xyz/web_accionar_xyz
   ```
2. Build the production build:
   ```bash
   npm run build
   ```
3. Upload files to the IONOS web server via SSH (use `cat | ssh` pattern to bypass strict SFTP file locks):
   * **Deploy HTML Index:**
     ```bash
     cat dist/index.html | ssh u116181580@access1003590403.webspace-data.io "cat > /homepages/14/d1003590403/htdocs/index.html"
     ```
   * **Deploy CSP .htaccess Rules:**
     ```bash
     cat dist/.htaccess | ssh u116181580@access1003590403.webspace-data.io "cat > /homepages/14/d1003590403/htdocs/.htaccess"
     ```
   * **Sync Compiled Assets:**
     Use `scp` or `rsync` to copy the updated compiled files under `dist/assets/` to the remote server `/homepages/14/d1003590403/htdocs/assets/`.

---

## 5. Troubleshooting & Technical Constraints

* **Missing Curl dependency:** The container's Python image is slim. If rebuilding, ensure `curl` is explicitly installed via `apt-get` in the `Dockerfile` to allow runtime calls to `worldcup26.ir`.
* **SSL Handshake Errors:** The `worldcup26.ir` API server rejects default Python SSL contexts (`urllib.request`), throwing an `EOF occurred in violation of protocol` error. Always use `curl -s -k` in subprocess calls to query this API.
* **Streamlit Caching:** The standings data is cached for 10 minutes (`@st.cache_data(ttl=600)`). If updates aren't appearing immediately on the live server, restart the Cloud Run container or append a random query parameter to the URL to force the browser/server cache to refresh.
