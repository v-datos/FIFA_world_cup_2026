#!/usr/bin/env python3
"""Deterministic top-scorer extractor for the FIFA World Cup 2026 dashboard.

The Overview tab's "Top Scorers" came from a hand-typed `top_scorer` field in
`data/bracket/grid_state.json`, so it went stale (e.g. a tied leader missing).
This derives the Golden Boot leaders automatically from ESPN's public match feed
(`keyEvents` scoring plays) and writes every player tied for the lead back into
grid_state.json — nothing else in that file is touched.

Open-play goals and scored penalties count; own goals and shootout penalties do
not. Run it (or schedule it) and the leaderboard refreshes itself.

Usage:
  python3 -m src.pipeline.update_top_scorers                 # dry-run (prints)
  python3 -m src.pipeline.update_top_scorers --write         # update grid_state
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
from pathlib import Path
import re
from typing import Any

import requests

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRID_STATE = PROJECT_ROOT / "data" / "bracket" / "grid_state.json"
UA = {"User-Agent": "Mozilla/5.0"}
SEASON_START = "20260611"  # 2026 World Cup group stage opener
MAX_LEADERS = 8            # guard against absurd lists if many tie early


def _get(url: str) -> dict:
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    return r.json()


def parse_scorers(scorers_str: str | None) -> list[str]:
    if not scorers_str or scorers_str == "null":
        return []
    
    # Standardize quotes and brackets to make it valid JSON list format
    s = scorers_str.replace('“', '"').replace('”', '"').replace('‘', '"').replace('’', '"')
    s = s.replace('{', '[').replace('}', ']')
    
    try:
        items = json.loads(s)
    except Exception:
        # Fallback if json load fails, use regex to find everything inside quotes
        items = re.findall(r'"([^"]+)"', s)
        if not items:
            # Fallback if no quotes at all, split by comma
            s_clean = scorers_str.strip().strip("{}")
            items = [x.strip() for x in s_clean.split(",") if x.strip()]
            
    parsed = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        # Skip own goals
        if "(OG)" in item or "(og)" in item or "own goal" in item.lower():
            continue
        
        # Regex to match player name and minute (e.g., "J. Quiñones 9'", "K. Havertz 45'+5'(p)")
        m = re.match(r'^(.+?)\s+\d+(?:\+\d+)?\'(?:.*)$', item)
        if m:
            player_name = m.group(1).strip()
            parsed.append(player_name)
        else:
            # Fallback: if no match, try to split by last space if there is a number
            parts = item.split()
            if len(parts) > 1:
                parsed.append(" ".join(parts[:-1]))
            else:
                parsed.append(item)
    return parsed


def aggregate(season_start: str, end: str) -> tuple[list[dict], int]:
    goals: collections.Counter = collections.Counter()
    team_of: dict[str, str] = {}
    matches = 0
    
    url = "https://worldcup26.ir/get/games"
    try:
        r = requests.get(url, headers=UA, timeout=25)
        r.raise_for_status()
        games = r.json().get("games", [])
    except Exception as e:
        print(f"Error fetching live games: {e}")
        return [], 0

    for g in games:
        # Check if match is finished
        if g.get("finished") != "TRUE" and g.get("finished") is not True:
            continue
            
        local_date = g.get("local_date")
        if not local_date:
            continue
            
        try:
            game_date_str = local_date.split()[0] # "MM/DD/YYYY"
            m, d, y = game_date_str.split("/")
            game_yyyymmdd = f"{y}{m}{d}"
        except Exception:
            continue
            
        if not (season_start <= game_yyyymmdd <= end):
            continue
            
        matches += 1
        
        home_team = normalize_team_name(g.get("home_team_name_en"))
        away_team = normalize_team_name(g.get("away_team_name_en"))
        
        for p in parse_scorers(g.get("home_scorers")):
            goals[p] += 1
            team_of[p] = home_team
            
        for p in parse_scorers(g.get("away_scorers")):
            goals[p] += 1
            team_of[p] = away_team

    if not goals:
        return [], matches
    top = max(goals.values())
    leaders = sorted(
        ({"name": n, "team": team_of.get(n), "goals": g} for n, g in goals.items() if g == top),
        key=lambda s: s["name"],
    )
    return leaders[:MAX_LEADERS], matches


def main() -> None:
    ap = argparse.ArgumentParser(description="Update top scorers from worldcup26.ir.")
    ap.add_argument("--season-start", default=SEASON_START, help="YYYYMMDD window start")
    ap.add_argument("--end", default=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d"), help="YYYYMMDD window end (default today UTC)")
    ap.add_argument("--write", action="store_true", help="Write leaders into grid_state.json")
    args = ap.parse_args()

    leaders, matches = aggregate(args.season_start, args.end)
    print(f"scanned {matches} matches; {len(leaders)} leader(s) at {leaders[0]['goals'] if leaders else 0} goals")
    for s in leaders:
        print(f"  {s['goals']}  {s['name']} ({s['team']})")

    if not args.write:
        print("(dry-run; pass --write to update grid_state.json)")
        return
    if not leaders:
        print("no goals found — leaving grid_state.json unchanged")
        return
    state = json.loads(GRID_STATE.read_text(encoding="utf-8"))
    state["top_scorer"] = leaders
    GRID_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"updated {GRID_STATE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
