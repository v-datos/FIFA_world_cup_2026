# DEC023 - Docker Frontend Build Must Include the Team Identity Contract

Date: 2026-06-19

## Status

Accepted.

## Context

The T-042 live deployment execution found that Cloud Run and `accionar.xyz`
were frozen at revision `fifa-2026-dashboard-00017-6z7`, deployed 2026-06-17,
which predates the T-027 team identity contract (2026-06-18). Every attempt to
deploy newer code failed, and the failure was silent because no deploy had been
run since T-027.

Root cause: `src/frontend/src/lib/teamIdentity.ts` imports the repo-canonical
contract with a cross-boundary relative path:

```ts
import teamIdentityData from '../../../../data/reference/team_identity.json';
```

The path reaches outside `src/frontend/` into the repo-level `data/` directory.
This resolves locally because `data/` is a sibling of `src/frontend/` in the
working tree. The Docker `frontend-builder` stage, however, only copied
`src/frontend/` into the image, so the JSON was absent and `tsc -b` failed:

```
src/lib/teamIdentity.ts(1,30): error TS2307: Cannot find module
'../../../../data/reference/team_identity.json'
```

`npm run build` returned exit code 2, failing Cloud Build step 0 before any
image was pushed or deployed.

The local verification gate `npm --prefix src/frontend run build` did not catch
this because it runs in the real repo, where `data/reference/team_identity.json`
exists at the expected relative location. Only the isolated Docker build context
exposes the missing file.

Duplicating the contract into `src/frontend/` was rejected: T-027 (DEC012)
deliberately centralized team identity as a single source of truth shared by the
Python and TypeScript consumers.

## Decision

Keep the single canonical contract at `data/reference/team_identity.json` and
make the Docker `frontend-builder` stage mirror the repo layout so the existing
relative import resolves the same way it does locally:

- Set `WORKDIR /build/src/frontend` so the frontend keeps its repo-relative
  position inside the image.
- `COPY data/reference/team_identity.json /build/data/reference/team_identity.json`
  before `npm run build`, so `../../../../data/...` resolves to
  `/build/data/reference/team_identity.json`.
- Copy the built assets from `/build/src/frontend/dist` in the final stage.

## Consequences

- The Docker image builds the frontend with the same module graph as local
  development, including the centralized identity contract.
- Any future frontend import that reaches outside `src/frontend/` into the repo
  must be mirrored into the Docker build context, or it will break the image
  build while passing the local gate.
- The local-only `npm run build` gate is necessary but not sufficient for
  deployment confidence. A Docker build (local `docker build` or Cloud Build) is
  the authoritative frontend bundling check.

## Verification

- Cloud Build `gcloud builds submit --config cloudbuild.yaml .` passes the
  `frontend-builder` stage and proceeds to backend assembly, image push, and
  Cloud Run deploy.
- Post-deploy Cloud Run smoke per `docs/deployment_verification_checklist.md`.
- `git diff --check`.
