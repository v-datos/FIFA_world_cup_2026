#!/usr/bin/env python3
"""Deterministic squad-average-age extractor for the FIFA World Cup 2026 dashboard.

`average_age` in the squad-style cache was hand-researched from Transfermarkt for
only 3 of 48 teams, leaving the rest MISSING. This derives it automatically from
ESPN: the squad is the union of every player who appeared for a team in the
tournament window, and each player's age comes from ESPN's athlete endpoint
(`dateOfBirth`). DOBs are cached so reruns only fetch new players.

It updates ONLY the `average_age` field of each team in
data/source_cache/squad_style/latest_metrics.json; the collector preserves it on
later runs (it merges, only rewriting the style metrics it computes).

Usage:
  python3 -m src.pipeline.update_team_ages                # dry-run (prints)
  python3 -m src.pipeline.update_team_ages --write        # update the cache
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
from typing import Optional

import requests

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
STYLE_CACHE = DATA_DIR / "source_cache" / "squad_style" / "latest_metrics.json"
DOB_CACHE = DATA_DIR / "source_cache" / "player_ages" / "dob_cache.json"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
ATHLETE = "https://sports.core.api.espn.com/v2/sports/soccer/athletes/{}"
UA = {"User-Agent": "Mozilla/5.0"}
SEASON_START = "20260611"


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


def squad_ids(season_start: str, end: str) -> dict[str, set[str]]:
    """Team display name -> set of ESPN athlete ids that appeared in the window."""
    squads: dict[str, set[str]] = collections.defaultdict(set)
    for day in _date_range(season_start, end):
        try:
            events = _get(f"{ESPN_BASE}/scoreboard?dates={day}").get("events", [])
        except requests.RequestException:
            continue
        for event in events:
            try:
                summary = _get(f"{ESPN_BASE}/summary?event={event['id']}")
            except (requests.RequestException, KeyError):
                continue
            for block in summary.get("rosters", []):
                team = (block.get("team") or {}).get("displayName")
                if not team:
                    continue
                for entry in block.get("roster", []):
                    aid = (entry.get("athlete") or {}).get("id")
                    if aid:
                        squads[team].add(str(aid))
    return squads


def load_dob_cache() -> dict[str, Optional[str]]:
    if DOB_CACHE.exists():
        return json.loads(DOB_CACHE.read_text(encoding="utf-8"))
    return {}


def fetch_dobs(ids: set[str], cache: dict[str, Optional[str]]) -> None:
    missing = [a for a in ids if a not in cache]

    def one(aid: str) -> tuple[str, Optional[str]]:
        try:
            return aid, _get(ATHLETE.format(aid)).get("dateOfBirth")
        except requests.RequestException:
            return aid, None

    if missing:
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            for aid, dob in ex.map(one, missing):
                cache[aid] = dob
        DOB_CACHE.parent.mkdir(parents=True, exist_ok=True)
        DOB_CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def average_ages(squads: dict[str, set[str]], cache: dict[str, Optional[str]]) -> dict[str, tuple[float, int]]:
    today = dt.datetime.now(dt.timezone.utc).date()
    out: dict[str, tuple[float, int]] = {}
    for team, ids in squads.items():
        ages = []
        for aid in ids:
            dob = cache.get(aid)
            if dob:
                ages.append((today - dt.date.fromisoformat(dob[:10])).days / 365.25)
        if ages:
            out[team] = (sum(ages) / len(ages), len(ages))
    return out


def write_cache(ages: dict[str, tuple[float, int]]) -> int:
    cache = json.loads(STYLE_CACHE.read_text(encoding="utf-8"))
    by_norm = {normalize_team_name(t["team"]): t for t in cache.get("teams", [])}
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated = 0
    for team, (avg, n) in ages.items():
        entry = by_norm.get(normalize_team_name(team))
        if not entry:
            continue
        entry.setdefault("fields", {})["average_age"] = {
            "value": round(avg, 1),
            "unit": "years",
            "status": "available",
            "source_label": "espn_derived",
            "source_name": f"ESPN squad roster DOBs (avg of {n} players)",
            "source_url": "https://sports.core.api.espn.com/v2/sports/soccer/athletes/{id}",
            "checked_at_utc": now,
            "retrieval_method": "espn_roster_dob",
        }
        updated += 1
    cache.setdefault("metadata", {})["field_record_count"] = sum(len(t.get("fields", {})) for t in cache["teams"])
    STYLE_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Derive squad average age from ESPN.")
    ap.add_argument("--season-start", default=SEASON_START)
    ap.add_argument("--end", default=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d"))
    ap.add_argument("--write", action="store_true", help="Update squad_style cache")
    args = ap.parse_args()

    squads = squad_ids(args.season_start, args.end)
    cache = load_dob_cache()
    all_ids = set().union(*squads.values()) if squads else set()
    fetch_dobs(all_ids, cache)
    ages = average_ages(squads, cache)

    print(f"teams with age: {len(ages)} / {len(squads)} squads; DOBs cached: {len(cache)}")
    for team in sorted(ages):
        avg, n = ages[team]
        print(f"  {team:24} {avg:.1f} ({n} players)")

    if not args.write:
        print("(dry-run; pass --write to update the squad_style cache)")
        return
    updated = write_cache(ages)
    print(f"updated average_age for {updated} teams in {STYLE_CACHE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
