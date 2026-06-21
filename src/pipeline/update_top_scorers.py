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
from typing import Any

import requests

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRID_STATE = PROJECT_ROOT / "data" / "bracket" / "grid_state.json"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
UA = {"User-Agent": "Mozilla/5.0"}
SEASON_START = "20260611"  # 2026 World Cup group stage opener
MAX_LEADERS = 8            # guard against absurd lists if many tie early


def _get(url: str) -> dict:
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    return r.json()


def _date_range(start: str, end: str) -> list[str]:
    d0 = dt.datetime.strptime(start, "%Y%m%d").date()
    d1 = dt.datetime.strptime(end, "%Y%m%d").date()
    if d1 < d0:
        return [start]
    return [(d0 + dt.timedelta(days=i)).strftime("%Y%m%d") for i in range((d1 - d0).days + 1)]


def _is_real_goal(ev: dict) -> bool:
    """A scoring play that counts toward the Golden Boot."""
    if not ev.get("scoringPlay") or ev.get("shootout"):
        return False
    type_info = ev.get("type") or {}
    blob = f"{type_info.get('type','')} {type_info.get('text','')} {ev.get('text','')}".lower()
    return "own" not in blob  # own goals are not credited to the scorer


def aggregate(season_start: str, end: str) -> tuple[list[dict], int]:
    goals: collections.Counter = collections.Counter()
    team_of: dict[str, str] = {}
    matches = 0
    for day in _date_range(season_start, end):
        try:
            events = _get(f"{ESPN_BASE}/scoreboard?dates={day}").get("events", [])
        except requests.RequestException:
            continue
        for event in events:
            matches += 1
            try:
                summary = _get(f"{ESPN_BASE}/summary?event={event['id']}")
            except (requests.RequestException, KeyError):
                continue
            for ev in summary.get("keyEvents", []):
                if not _is_real_goal(ev):
                    continue
                participants = ev.get("participants") or []
                if not participants:
                    continue
                athlete = (participants[0] or {}).get("athlete") or {}
                name = athlete.get("displayName")
                if not name:
                    continue
                goals[name] += 1
                team_of[name] = normalize_team_name((ev.get("team") or {}).get("displayName"))

    if not goals:
        return [], matches
    top = max(goals.values())
    leaders = sorted(
        ({"name": n, "team": team_of.get(n), "goals": g} for n, g in goals.items() if g == top),
        key=lambda s: s["name"],
    )
    return leaders[:MAX_LEADERS], matches


def main() -> None:
    ap = argparse.ArgumentParser(description="Update top scorers from ESPN.")
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
