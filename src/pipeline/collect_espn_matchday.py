#!/usr/bin/env python3
"""Deterministic matchday collector for the FIFA World Cup 2026 dashboard.

Pulls fixtures, team style metrics, and lineups for a given date from ESPN's
public soccer API (no browser, no auth, no anti-bot blocking) and writes them to
the source caches the API already reads. This replaces per-matchday manual
research: run it (or schedule it) each day and the dashboard refreshes itself.

Sources written:
  - data/matches/{match_id}/summary.json   (venue + kickoff_utc, created if new)
  - data/source_cache/squad_style/latest_metrics.json   (style metrics)
  - data/source_cache/lineups/latest.json               (starting XI + formation)

Usage:
  python3 src/pipeline/collect_espn_matchday.py            # dry-run, today
  python3 src/pipeline/collect_espn_matchday.py --date 20260620 --write
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Optional

import requests

from src.common.team_identity import canonical_team_slug, normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
UA = {"User-Agent": "Mozilla/5.0"}


def _get(url: str) -> dict:
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    return r.json()


def _num(value: Any) -> Optional[float]:
    try:
        return float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def fetch_scoreboard(date_yyyymmdd: str) -> list[dict]:
    data = _get(f"{ESPN_BASE}/scoreboard?dates={date_yyyymmdd}")
    return data.get("events", [])


def parse_event(event: dict) -> Optional[dict]:
    comp = (event.get("competitions") or [{}])[0]
    competitors = comp.get("competitors", [])
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None
    t1 = normalize_team_name(home.get("team", {}).get("displayName"))
    t2 = normalize_team_name(away.get("team", {}).get("displayName"))
    venue = comp.get("venue", {}) or {}
    city = (venue.get("address", {}) or {}).get("city")
    venue_name = venue.get("fullName")
    venue_str = f"{venue_name}, {city}" if venue_name and city else (venue_name or "")
    status = (comp.get("status", {}) or {}).get("type", {}).get("state")  # pre/in/post
    return {
        "event_id": event.get("id"),
        "team1": t1,
        "team2": t2,
        "match_id": f"{canonical_team_slug(t1)}_{canonical_team_slug(t2)}_2026",
        "venue": venue_str,
        "kickoff_utc": event.get("date"),  # ISO UTC
        "status": status,
        "score1": _num(home.get("score")),
        "score2": _num(away.get("score")),
    }


def team_style_from_stats(stats: dict, opp_stats: dict, goals: Optional[float], conceded: Optional[float]) -> dict:
    """Map ESPN boxscore stats to the project's team_metrics fields."""
    poss = _num(stats.get("possessionPct"))
    shots = _num(stats.get("totalShots"))
    sot = _num(stats.get("shotsOnTarget"))
    passes = _num(stats.get("totalPasses"))
    accurate = _num(stats.get("accuratePasses"))
    # ESPN's passPct displayValue is a coarse rounded ratio (e.g. "0.9"); compute
    # the real completion % from accurate/total passes instead.
    pass_pct = round(accurate / passes * 100, 1) if accurate is not None and passes else None
    opp_shots = _num(opp_stats.get("totalShots"))
    out: dict[str, float] = {}
    if poss is not None:
        out["possession_avg"] = poss
    if shots is not None:
        out["shots_per_90"] = shots
    if shots and sot is not None:
        out["shots_on_target_pct"] = round(sot / shots * 100, 1)
    if passes is not None:
        out["passes_per_90"] = passes
    if pass_pct is not None:
        out["pass_completion_pct"] = pass_pct
    if goals is not None:
        out["goals_per_90"] = goals
    if conceded is not None:
        out["goals_conceded_per_90"] = conceded
    if opp_shots is not None:
        out["shots_against_per_90"] = opp_shots
    return out


def lineup_from_roster(roster_entry: dict) -> Optional[dict]:
    formation = roster_entry.get("formation")
    players = [p for p in roster_entry.get("roster", []) if p.get("starter")]
    if not players:
        return None
    ordered = []
    for p in players:
        ath = p.get("athlete", {}) or {}
        name = ath.get("displayName")
        if not name:
            continue
        ordered.append({"name": name, "club": "N/A"})
    if len(ordered) < 7:
        return None
    return {"formation": formation or "4-3-3", "players": ordered}


STAT_LIST = lambda team: {s.get("name"): s.get("displayValue") for s in team.get("statistics", [])}


def collect(date_yyyymmdd: str) -> dict:
    """Return a manifest of fixtures, style metrics, and lineups for the date."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fixtures = []
    style: dict[str, dict] = {}
    lineups: dict[str, dict] = {}
    for event in fetch_scoreboard(date_yyyymmdd):
        fx = parse_event(event)
        if not fx:
            continue
        fixtures.append(fx)
        if fx["status"] == "pre":
            continue  # not played yet: fixture only, no stats/lineup
        try:
            summary = _get(f"{ESPN_BASE}/summary?event={fx['event_id']}")
        except requests.RequestException:
            continue
        teams = (summary.get("boxscore", {}) or {}).get("teams", [])
        by_name = {normalize_team_name(t.get("team", {}).get("displayName")): t for t in teams}
        s1, s2 = by_name.get(fx["team1"]), by_name.get(fx["team2"])
        if s1 and s2:
            st1, st2 = STAT_LIST(s1), STAT_LIST(s2)
            style[fx["team1"]] = team_style_from_stats(st1, st2, fx["score1"], fx["score2"])
            style[fx["team2"]] = team_style_from_stats(st2, st1, fx["score2"], fx["score1"])
        for r in summary.get("rosters", []):
            tname = normalize_team_name(r.get("team", {}).get("displayName"))
            lu = lineup_from_roster(r)
            if tname and lu:
                lineups[tname] = lu
    return {"date": date_yyyymmdd, "checked_at_utc": now, "fixtures": fixtures,
            "style": style, "lineups": lineups}


def _load(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def write_caches(manifest: dict) -> list[str]:
    now = manifest["checked_at_utc"]
    written = []
    # 1) squad/style cache
    sp = DATA_DIR / "source_cache" / "squad_style" / "latest_metrics.json"
    S = _load(sp, {"metadata": {}, "teams": []})
    ex = {t["team"]: t for t in S.get("teams", [])}
    for team, fields in manifest["style"].items():
        t = ex.get(team)
        if not t:
            t = {"team": team, "fixture_ids": [], "fields": {}}
            S["teams"].append(t)
            ex[team] = t
        t.setdefault("fields", {})
        for k, v in fields.items():
            t["fields"][k] = {"value": v, "status": "available", "source_label": "web_researched",
                              "source_name": "ESPN match boxscore", "source_url": ESPN_BASE,
                              "checked_at_utc": now, "retrieval_method": "espn_api"}
        t["status"] = "partial"
    S.setdefault("metadata", {})
    S["metadata"]["checked_at_utc"] = now
    S["metadata"]["field_record_count"] = sum(len(t.get("fields", {})) for t in S["teams"])
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(S, f, indent=2, ensure_ascii=False)
    written.append(str(sp.relative_to(PROJECT_ROOT)))
    # 2) lineup cache
    lp = DATA_DIR / "source_cache" / "lineups" / "latest.json"
    L = _load(lp, {"metadata": {}, "teams": {}})
    for team, lu in manifest["lineups"].items():
        L.setdefault("teams", {})[canonical_team_slug(team)] = {
            "formation": lu["formation"], "manager": "", "philosophy": "Confirmed XI from ESPN match data.",
            "source_label": "web_researched", "source_url": ESPN_BASE, "checked_at_utc": now,
            "players": lu["players"]}
    L.setdefault("metadata", {})["checked_at_utc"] = now
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(L, f, indent=2, ensure_ascii=False)
    written.append(str(lp.relative_to(PROJECT_ROOT)))
    # 3) fixture folders (venue + kickoff_utc), do not overwrite curated summaries
    for fx in manifest["fixtures"]:
        folder = DATA_DIR / "matches" / fx["match_id"]
        sjson = folder / "summary.json"
        if sjson.exists():
            with open(sjson, "r", encoding="utf-8") as f:
                data = json.load(f)
            md = data.setdefault("metadata", {})
            if fx["venue"]:
                md["venue"] = fx["venue"]
            md["kickoff_utc"] = fx["kickoff_utc"]
            with open(sjson, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            written.append(str(sjson.relative_to(PROJECT_ROOT)))
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="Collect matchday data from ESPN.")
    ap.add_argument("--date", default=dt.datetime.now().strftime("%Y%m%d"),
                    help="YYYYMMDD (default: today)")
    ap.add_argument("--write", action="store_true", help="Persist to caches (default: dry-run)")
    args = ap.parse_args()
    manifest = collect(args.date)
    print(f"date={manifest['date']} fixtures={len(manifest['fixtures'])} "
          f"style_teams={len(manifest['style'])} lineup_teams={len(manifest['lineups'])}")
    for fx in manifest["fixtures"]:
        print(f"  {fx['match_id']:36} {fx['status']:4} venue={fx['venue']!r} kickoff={fx['kickoff_utc']}")
    if args.write:
        written = write_caches(manifest)
        print("WROTE:")
        for w in written:
            print("  ", w)
    else:
        print("(dry-run; pass --write to persist)")


if __name__ == "__main__":
    main()
