# Cloud Build Trigger — Auto-Deploy on Push to `main`

Last updated: 2026-06-20

This one-time setup makes every push to `main` rebuild and deploy to Cloud Run
automatically. Combined with the daily `matchday-refresh` GitHub Action (which
pushes refreshed data), this closes the loop: **data → live, with zero manual
steps.**

Project facts:

| Item | Value |
|---|---|
| GCP project | `midyear-castle-328020` |
| Repository | GitHub `v-datos/FIFA_world_cup_2026` |
| Build config | `cloudbuild.yaml` (already builds + deploys) |
| Cloud Run service | `fifa-2026-dashboard` (region `us-central1`) |

## Step 1 — Connect the GitHub repo to Cloud Build

1. Open the Cloud Build Triggers page:
   `https://console.cloud.google.com/cloud-build/triggers?project=midyear-castle-328020`
2. Confirm the project at the top is **midyear-castle-328020**.
3. Click **Connect Repository** (top of the page). If you don't see it, click
   **Manage repositories → Connect host → GitHub (Cloud Build GitHub App)**.
4. Choose source **GitHub (Cloud Build GitHub App)**, click **Continue**.
5. A GitHub window opens. Sign in, then **Install/Authorize Google Cloud Build**.
   - Choose **Only select repositories** → pick **v-datos/FIFA_world_cup_2026**.
   - Click **Install** / **Save**.
6. Back in Cloud Build, tick **v-datos/FIFA_world_cup_2026**, accept the terms,
   and click **Connect**.

## Step 2 — Create the trigger

1. Still on Triggers, click **Create Trigger**.
2. Fill in:
   - **Name:** `deploy-on-push-main`
   - **Region:** `global` (or `us-central1`)
   - **Event:** **Push to a branch**
   - **Source → Repository:** `v-datos/FIFA_world_cup_2026`
   - **Branch:** `^main$`
   - **Configuration → Type:** **Cloud Build configuration file (yaml or json)**
   - **Location:** **Repository**, file path: `cloudbuild.yaml`
3. Leave the **Service account** as the default Cloud Build service account
   (deploys via `gcloud builds submit` already work, so it has the needed Cloud
   Run permissions).
4. Click **Create**.

## Step 3 — Verify permissions (only if a build fails)

The build's deploy step runs `gcloud run deploy`, so the trigger's service
account needs:

- **Cloud Run Admin** (`roles/run.admin`)
- **Service Account User** (`roles/iam.serviceAccountUser`)

These are already in place (manual `gcloud builds submit` deploys succeed). If a
triggered build fails on the deploy step with a permissions error, grant those
two roles to the Cloud Build service account at
`https://console.cloud.google.com/iam-admin/iam?project=midyear-castle-328020`.

## Step 4 — Test it

1. On the Triggers page, click **Run** next to `deploy-on-push-main` (or just
   push any commit to `main`).
2. Watch **Cloud Build → History**: the build should run all three steps
   (build → push → deploy) and finish **SUCCESS**.
3. Confirm a new Cloud Run revision is serving:
   `https://console.cloud.google.com/run/detail/us-central1/fifa-2026-dashboard/revisions?project=midyear-castle-328020`

## How the full chain works after this

1. Twice a day the **matchday-refresh** GitHub Action runs the ESPN collector and
   pushes the refreshed data to `main`.
2. That push fires the Cloud Build trigger (Cloud Build receives the GitHub
   webhook; this is independent of GitHub Actions' own loop-prevention).
3. Cloud Build rebuilds and deploys → the live dashboard reflects the new data.

No manual action per matchday.

## To pause auto-deploy

Cloud Build → Triggers → toggle `deploy-on-push-main` to **Disabled** (data still
refreshes in the repo; it just won't auto-deploy until re-enabled).
