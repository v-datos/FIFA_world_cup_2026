#!/usr/bin/env python3
"""Deterministic matchday collector for the FIFA World Cup 2026 dashboard.

Pulls fixtures, team style metrics, and lineups from ESPN's public soccer API
(no browser, no auth, no anti-bot blocking) and writes them to the source caches
the API already reads. Replaces per-matchday manual research: run it (or schedule
it) and the dashboard refreshes itself.

Team style metrics are AVERAGED across every match a team has played in the
tournament window (not just the latest game). ESPN does not expose xG, so
xG/PPDA/field-tilt remain missing; market value/age stay Transfermarkt-sourced.

Sources written:
  - data/matches/{match_id}/summary.json   (venue + kickoff_utc)
  - data/source_cache/squad_style/latest_metrics.json   (averaged style metrics)
  - data/source_cache/lineups/latest.json               (latest XI + formation)

Usage:
  python3 -m src.pipeline.collect_espn_matchday                       # dry-run, today
  python3 -m src.pipeline.collect_espn_matchday --date 20260620 --write
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
SEASON_START = "20260611"  # 2026 World Cup group stage opener


def _get(url: str) -> dict:
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    return r.json()


def _num(value: Any) -> Optional[float]:
    try:
        return float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _date_range(start: str, end: str) -> list[str]:
    d0 = dt.datetime.strptime(start, "%Y%m%d").date()
    d1 = dt.datetime.strptime(end, "%Y%m%d").date()
    return [(d0 + dt.timedelta(days=i)).strftime("%Y%m%d")
            for i in range((d1 - d0).days + 1)] if d1 >= d0 else [end]


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
    return {
        "event_id": event.get("id"),
        "team1": t1,
        "team2": t2,
        "match_id": f"{canonical_team_slug(t1)}_{canonical_team_slug(t2)}_2026",
        "venue": venue_str,
        "kickoff_utc": event.get("date"),
        "status": (comp.get("status", {}) or {}).get("type", {}).get("state"),  # pre/in/post
        "score1": _num(home.get("score")),
        "score2": _num(away.get("score")),
    }


def _stat_map(team: dict) -> dict:
    return {s.get("name"): s.get("displayValue") for s in team.get("statistics", [])}


def raw_match_stats(team_box: dict, opp_box: dict, goals: Optional[float], conceded: Optional[float]) -> dict:
    st, ost = _stat_map(team_box), _stat_map(opp_box)
    return {
        "possession": _num(st.get("possessionPct")),
        "shots": _num(st.get("totalShots")),
        "sot": _num(st.get("shotsOnTarget")),
        "passes": _num(st.get("totalPasses")),
        "accurate": _num(st.get("accuratePasses")),
        "goals": goals,
        "conceded": conceded,
        "opp_shots": _num(ost.get("totalShots")),
    }


def average_team(rows: list[dict]) -> dict:
    """Average a team's per-match raw stats into the project's metric fields."""
    def mean(key: str) -> Optional[float]:
        vals = [r[key] for r in rows if r.get(key) is not None]
        return sum(vals) / len(vals) if vals else None

    def total(key: str) -> float:
        return sum(r[key] for r in rows if r.get(key) is not None)

    out: dict[str, float] = {}
    poss, shots, sot = mean("possession"), mean("shots"), mean("sot")
    passes, goals, conceded = mean("passes"), mean("goals"), mean("conceded")
    opp_shots = mean("opp_shots")
    tot_shots, tot_sot = total("shots"), total("sot")
    tot_passes, tot_acc = total("passes"), total("accurate")
    if poss is not None:
        out["possession_avg"] = round(poss, 1)
    if shots is not None:
        out["shots_per_90"] = round(shots, 1)
    if tot_shots:
        out["shots_on_target_pct"] = round(tot_sot / tot_shots * 100, 1)
    if passes is not None:
        out["passes_per_90"] = round(passes, 0)
    if tot_passes:
        out["pass_completion_pct"] = round(tot_acc / tot_passes * 100, 1)
    if goals is not None:
        out["goals_per_90"] = round(goals, 2)
    if conceded is not None:
        out["goals_conceded_per_90"] = round(conceded, 2)
    if opp_shots is not None:
        out["shots_against_per_90"] = round(opp_shots, 1)
    return out


def lineup_from_roster(roster_entry: dict) -> Optional[dict]:
    formation = roster_entry.get("formation")
    players = [p for p in roster_entry.get("roster", []) if p.get("starter")]
    ordered = []
    for p in players:
        name = (p.get("athlete", {}) or {}).get("displayName")
        if name:
            ordered.append({"name": name, "club": "N/A"})  # ESPN match feed has no club
    if len(ordered) < 7:
        return None
    return {"formation": formation or "4-3-3", "players": ordered}


def collect(active_date: str, season_start: str = SEASON_START) -> dict:
    """Gather active-date fixtures plus tournament-averaged style metrics + lineups."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # 1) Active-date fixtures (for venue/kickoff folder updates).
    active_fixtures = [fx for ev in fetch_events(active_date) if (fx := parse_event(ev))]
    # 2) All completed events across the tournament window (dedup by id).
    completed: dict[str, dict] = {}
    for day in _date_range(season_start, active_date):
        for ev in fetch_events(day):
            fx = parse_event(ev)
            if fx and fx["status"] == "post" and fx["event_id"] not in completed:
                completed[fx["event_id"]] = {**fx, "day": day}
    # 3) Accumulate per-team raw stats + latest lineup.
    team_rows: dict[str, list[dict]] = {}
    lineups: dict[str, dict] = {}
    lineup_day: dict[str, str] = {}
    for fx in completed.values():
        try:
            summary = _get(f"{ESPN_BASE}/summary?event={fx['event_id']}")
        except requests.RequestException:
            continue
        teams = (summary.get("boxscore", {}) or {}).get("teams", [])
        by_name = {normalize_team_name(t.get("team", {}).get("displayName")): t for t in teams}
        b1, b2 = by_name.get(fx["team1"]), by_name.get(fx["team2"])
        if b1 and b2:
            team_rows.setdefault(fx["team1"], []).append(raw_match_stats(b1, b2, fx["score1"], fx["score2"]))
            team_rows.setdefault(fx["team2"], []).append(raw_match_stats(b2, b1, fx["score2"], fx["score1"]))
        for r in summary.get("rosters", []):
            tname = normalize_team_name(r.get("team", {}).get("displayName"))
            lu = lineup_from_roster(r)
            if tname and lu and fx["day"] >= lineup_day.get(tname, ""):
                lineups[tname] = lu
                lineup_day[tname] = fx["day"]
    style = {team: average_team(rows) for team, rows in team_rows.items() if rows}
    matches_counted = {team: len(rows) for team, rows in team_rows.items()}
    return {"date": active_date, "checked_at_utc": now, "fixtures": active_fixtures,
            "style": style, "lineups": lineups, "matches_counted": matches_counted}


def fetch_events(date_yyyymmdd: str) -> list[dict]:
    try:
        return _get(f"{ESPN_BASE}/scoreboard?dates={date_yyyymmdd}").get("events", [])
    except requests.RequestException:
        return []


def _load(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def write_caches(manifest: dict) -> list[str]:
    now = manifest["checked_at_utc"]
    written = []
    sp = DATA_DIR / "source_cache" / "squad_style" / "latest_metrics.json"
    S = _load(sp, {"metadata": {}, "teams": []})
    ex = {t["team"]: t for t in S.get("teams", [])}
    for team, fields in manifest["style"].items():
        t = ex.get(team) or {"team": team, "fixture_ids": [], "fields": {}}
        if team not in ex:
            S["teams"].append(t)
            ex[team] = t
        t.setdefault("fields", {})
        n = manifest["matches_counted"].get(team, 1)
        for k, v in fields.items():
            t["fields"][k] = {"value": v, "status": "available", "source_label": "web_researched",
                              "source_name": f"ESPN match boxscore (avg of {n} match{'es' if n != 1 else ''})",
                              "source_url": ESPN_BASE, "checked_at_utc": now, "retrieval_method": "espn_api"}
        t["status"] = "partial"
    S.setdefault("metadata", {})["checked_at_utc"] = now
    S["metadata"]["field_record_count"] = sum(len(t.get("fields", {})) for t in S["teams"])
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(S, f, indent=2, ensure_ascii=False)
    written.append(str(sp.relative_to(PROJECT_ROOT)))

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

    for fx in manifest["fixtures"]:
        sjson = DATA_DIR / "matches" / fx["match_id"] / "summary.json"
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
    ap.add_argument("--date", default=dt.datetime.now().strftime("%Y%m%d"), help="YYYYMMDD (default: today)")
    ap.add_argument("--season-start", default=SEASON_START, help="YYYYMMDD averaging window start")
    ap.add_argument("--write", action="store_true", help="Persist to caches (default: dry-run)")
    args = ap.parse_args()
    manifest = collect(args.date, args.season_start)
    print(f"date={manifest['date']} active_fixtures={len(manifest['fixtures'])} "
          f"style_teams={len(manifest['style'])} lineup_teams={len(manifest['lineups'])}")
    for team in sorted(manifest["style"]):
        n = manifest["matches_counted"].get(team, 0)
        f = manifest["style"][team]
        print(f"  {team:18} ({n} matches) poss={f.get('possession_avg')} shots={f.get('shots_per_90')} "
              f"sot%={f.get('shots_on_target_pct')} pass%={f.get('pass_completion_pct')}")
    if args.write:
        written = write_caches(manifest)
        print("WROTE:", *written, sep="\n  ")
    else:
        print("(dry-run; pass --write to persist)")


if __name__ == "__main__":
    main()
