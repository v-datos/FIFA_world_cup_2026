# DEC031 - Injuries & Player Clubs via Gemini + Google Search Grounding

Date: 2026-06-21

## Status

Accepted.

## Context

Two dashboard fields had no automated source and were hand-curated / hardcoded:
- **Injuries** (`ai_summary.injuries`) — hand-curated for 23 of 54 matches.
- **Player clubs** — an 86-entry hardcoded map in `InteractivePitch.tsx`; the
  lineup cache carried `club: "N/A"`.

No free structured API provides national-team injuries or current squad clubs:
FotMob exposes neither for internationals (its only "injur" reference is
"injury time"); FBref/Sofascore/Transfermarkt-live are IP-blocked from CI. But
**Gemini with Google Search grounding** can retrieve both from live web sources
and cite them — grounded, not hallucinated (verified: it returned Germany's
Gnabry/Schlotterbeck injuries with FourFourTwo/FoxSports citations).

## Decision

Add `src/pipeline/generate_team_news.py`. For each team in a date's fixtures it
makes a **two-step** Gemini call (Google Search grounding and JSON output cannot
be combined in one request): step 1 retrieves injuries + squad clubs as
web-grounded prose; step 2 structures that prose into JSON. It writes:

- injuries → the match `summary.json` `ai_summary.injuries[slug]`
  (`injuries_source: ai_web_grounded`; "No confirmed injuries reported." when none),
- player clubs → the lineup cache players' `club` field, matched by normalized name.

`collect_espn_matchday` now **preserves** an existing manager and player clubs
when it rewrites a lineup entry, so the daily ESPN run does not wipe them. Wired
into the matchday Action behind the existing `GCP_SA_KEY` gate (uses
`google-genai`); skipped without credentials.

## Consequences

- Injuries and clubs are now AI-sourced and refresh per matchday (e.g. Spain:
  Lamine Yamal hamstring-Doubtful; Uruguay: Arrascaeta broken collarbone; clubs:
  Cucurella→Chelsea, Cubarsí→Barcelona).
- These are **best-effort, web-grounded** — labelled `ai_web_grounded`, not an
  authoritative feed; quality depends on what reporting exists at run time.
- Two Gemini calls per team per matchday (grounded + structuring); only teams
  playing that day are queried, so volume is small.
- The hardcoded frontend club map remains as a fallback for unmatched names.

## Verification

- `python3 -m src.pipeline.generate_team_news --date 20260621 --write` →
  injuries + ~26 clubs/team; `/api/match/spain_saudi_arabia_2026/summary` serves
  both. Collector preserves clubs (Spain 11 → 11 after a collector run).
