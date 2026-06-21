#!/usr/bin/env python3
"""Current squad news (injuries + player clubs) via Gemini + Google Search grounding.

Injuries and player clubs have no free structured API (FotMob exposes neither for
national teams; FBref/Sofascore/Transfermarkt are IP-blocked from CI). But Gemini
with Google Search grounding can retrieve them from live web sources and cite
them — not hallucinate. For each team in a date's fixtures it makes one grounded
call returning verified injuries + each squad player's current club, then writes:

- injuries  -> the match's summary.json `ai_summary.injuries[slug]`
- clubs     -> the lineups cache players' `club` field (matched by name)

Both are labelled as AI-sourced (best-effort, web-grounded). Needs Google Cloud
credentials (ADC locally, or the GCP_SA_KEY GitHub secret). Dry-run by default.

Usage:
  python3 -m src.pipeline.generate_team_news --date 20260621            # dry-run
  python3 -m src.pipeline.generate_team_news --date 20260621 --write
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import unicodedata
from pathlib import Path

from src.common.team_identity import canonical_team_slug

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LINEUPS_CACHE = DATA_DIR / "source_cache" / "lineups" / "latest.json"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
PROJECT = os.environ.get("GEMINI_PROJECT", "statsbomb-db")
LOCATION = os.environ.get("GEMINI_LOCATION", "us-central1")


def _norm_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


def _load(path: Path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


_STRUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "injuries": {"type": "array", "items": {"type": "string"}},
        "clubs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"player": {"type": "string"}, "club": {"type": "string"}},
                "required": ["player", "club"],
            },
        },
    },
    "required": ["injuries", "clubs"],
}


def fetch_news(team: str) -> dict:
    """Grounded retrieval + structuring -> {'injuries': [...], 'clubs': {name: club}}.

    Google Search grounding and JSON output can't be combined in one Gemini call,
    so step 1 retrieves the facts as prose (web-grounded) and step 2 structures
    that prose into JSON (no tools).
    """
    from google import genai
    from google.genai import types

    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    search_prompt = (
        f"Using current web sources, for {team}'s squad at the 2026 FIFA World Cup:\n"
        "1. List any verified, recent injuries or suspensions affecting the squad — for each: "
        "player name, reason, and whether they are Out or Doubtful. If none are reported, say so.\n"
        "2. List every player in the announced World Cup squad with the club they currently play for."
    )
    grounded = client.models.generate_content(
        model=MODEL,
        contents=search_prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
            max_output_tokens=2500,
        ),
    )
    text = (grounded.text or "").strip()
    if not text:
        return {"injuries": [], "clubs": {}}

    structured = client.models.generate_content(
        model=MODEL,
        contents=(
            "Convert this report into JSON. injuries: array of strings formatted "
            "'Player Name (reason - Out)' or '(reason - Doubtful)', empty array if none. "
            "clubs: array of {player, club} for every player listed.\n\nReport:\n" + text
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_STRUCT_SCHEMA,
            temperature=0.0,
        ),
    )
    data = json.loads(structured.text or "{}")
    injuries = [str(x).strip() for x in (data.get("injuries") or []) if str(x).strip()][:8]
    clubs = {
        str(c["player"]).strip(): str(c["club"]).strip()
        for c in (data.get("clubs") or [])
        if c.get("player") and c.get("club")
    }
    return {"injuries": injuries, "clubs": clubs}


def write_injuries(match_id: str, slug: str, injuries: list[str]) -> bool:
    path = DATA_DIR / "matches" / match_id / "summary.json"
    summary = _load(path)
    if not summary:
        return False
    ai = summary.setdefault("ai_summary", {})
    ai.setdefault("injuries", {})[slug] = injuries or ["No confirmed injuries reported."]
    ai["injuries_source"] = "ai_web_grounded"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def write_clubs(team: str, clubs: dict) -> int:
    L = _load(LINEUPS_CACHE) or {"teams": {}}
    entry = L.get("teams", {}).get(canonical_team_slug(team))
    if not entry or not clubs:
        return 0
    by_norm = {_norm_name(k): v for k, v in clubs.items()}
    updated = 0
    for player in entry.get("players", []):
        club = by_norm.get(_norm_name(player.get("name", "")))
        if club:
            player["club"] = club
            updated += 1
    LINEUPS_CACHE.write_text(json.dumps(L, indent=2, ensure_ascii=False), encoding="utf-8")
    return updated


def _fixtures_on(date_yyyymmdd: str) -> list[dict]:
    target = dt.datetime.strptime(date_yyyymmdd, "%Y%m%d").strftime("%m/%d/%Y")
    out = []
    for folder in sorted((DATA_DIR / "matches").glob("*_2026")):
        meta = (_load(folder / "summary.json") or {}).get("metadata", {})
        if meta.get("date") == target and meta.get("team1") and meta.get("team2"):
            out.append({"match_id": folder.name, "team1": meta["team1"], "team2": meta["team2"]})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch injuries + player clubs via Gemini grounded search.")
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d"), help="YYYYMMDD fixtures")
    ap.add_argument("--write", action="store_true", help="Persist to summary.json + lineups cache")
    args = ap.parse_args()

    fixtures = _fixtures_on(args.date)
    print(f"model={MODEL} date={args.date} fixtures={len(fixtures)} mode={'write' if args.write else 'dry-run'}")
    seen: set[str] = set()
    for fx in fixtures:
        for team in (fx["team1"], fx["team2"]):
            slug = canonical_team_slug(team)
            try:
                news = fetch_news(team)
            except Exception as e:
                print(f"  {team}: fetch failed ({type(e).__name__}: {str(e)[:80]})")
                continue
            print(f"  {team}: {len(news['injuries'])} injuries, {len(news['clubs'])} clubs")
            for inj in news["injuries"][:3]:
                print(f"      - {inj}")
            if args.write:
                write_injuries(fx["match_id"], slug, news["injuries"])
                if team not in seen:
                    n = write_clubs(team, news["clubs"])
                    print(f"      clubs written to lineup: {n}")
            seen.add(team)
    if not args.write:
        print("(dry-run; set --write and ensure Google Cloud credentials to persist)")


if __name__ == "__main__":
    main()
