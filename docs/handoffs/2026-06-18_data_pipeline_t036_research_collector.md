# Handoff - T-036 Source-Backed Research Collector Prototype

Date: 2026-06-18  
Owner: Data Pipeline Engineer  
Reviewers: Football Data Scientist, QA / Reproducibility Engineer  
Status: Complete

## Summary

Added a one-fixture source-backed research collector:

```bash
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-file /path/to/source.json --dry-run
```

Write mode is explicit:

```bash
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-file /path/to/source.json --write
```

## What Changed

- Added `src/pipeline/collect_match_research.py`.
- Default mode is dry-run.
- Default write target is `data/matches/{match_id}/research_cache.json`.
- The collector refuses `summary.json`, `metrics.json`, and production
  `briefing.json` as write targets.
- Offline source files can be structured JSON claims or HTML/text scanned with
  conservative matchday keywords.
- Optional `--source-url` uses simple public HTTP GET and records blocked
  source records when unavailable.
- Source records retain source id/name, URL/path, collection method,
  checked-at time, status, source label, warnings, blocked reasons, and claim
  scope.
- Claim records retain claim type, text, basis, source ids, confidence, and
  draft review status.
- The cache embeds a proposed briefing draft for review instead of mutating
  `briefing.json`.

## Verification

Commands run:

```bash
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-file /tmp/t036_canada_qatar_source.json --now 2026-06-18T13:00
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-url https://www.theguardian.com/football/2026/jun/17/canada-qatar-world-cup-team-news-alphonso-davies --now 2026-06-18T10:30
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-file /tmp/t036_canada_qatar_source.json --now 2026-06-18T13:00 --write --data-dir /tmp/fwc26_t036_verify_20260618_1940/matches
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-file /tmp/t036_canada_qatar_source.json --output-path data/matches/canada_qatar_2026/briefing.json
cmp data/matches/canada_qatar_2026/summary.json /tmp/fwc26_t036_verify_20260618_1940/matches/canada_qatar_2026/summary.json
cmp data/matches/canada_qatar_2026/metrics.json /tmp/fwc26_t036_verify_20260618_1940/matches/canada_qatar_2026/metrics.json
python3 -m json.tool /tmp/fwc26_t036_verify_20260618_1940/matches/canada_qatar_2026/research_cache.json
python3 -m compileall -q src
npm --prefix src/frontend run build
```

Results:

- Offline dry-run emitted a valid manifest with two draft claims.
- Live URL dry-run succeeded after network approval and retained a
  `web_researched` source record plus draft source-backed claims.
- Temp write mode created only `research_cache.json`.
- Copied `summary.json` and `metrics.json` stayed byte-identical to the
  originals.
- Production `briefing.json` output was blocked.
- Python compile passed.
- Frontend build passed with the existing chunk-size warning only.

## Not Included

- No production `research_cache.json` files were written.
- No API route or frontend consumer was added.
- No paid-provider integration was added.
- No source-backed claim was approved for publication.

## Next Routing

- Football Data Scientist should review claim taxonomy and confidence language
  before any copied briefing content is approved.
- T-033 remains the API/UI task for briefing exposure.
- T-038 and T-039 remain responsible for squad/style metric source integration
  and no-cost provider feasibility.
