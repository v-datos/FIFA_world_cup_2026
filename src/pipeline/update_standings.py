#!/usr/bin/env python3
"""Deterministic standings and bracket updater for the FIFA World Cup 2026 dashboard.

Derives group standings and knockout bracket progression automatically from ESPN's
public match feed and writes them back into grid_state.json.

Usage:
  python3 -m src.pipeline.update_standings                 # dry-run (prints)
  python3 -m src.pipeline.update_standings --write         # update grid_state
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Optional

import requests

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRID_STATE = PROJECT_ROOT / "data" / "bracket" / "grid_state.json"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
UA = {"User-Agent": "Mozilla/5.0"}
SEASON_START = "20260611"

R32_SLOT_DEFS = {
    "r32_1": {"team1_role": "Runner-up Group A", "team2_role": "Runner-up Group B"},
    "r32_2": {"team1_role": "Winner Group C", "team2_role": "Runner-up Group F"},
    "r32_3": {"team1_role": "Winner Group E", "team2_allowed_groups": ["A", "B", "C", "D", "F"]},
    "r32_4": {"team1_role": "Winner Group F", "team2_role": "Runner-up Group C"},
    "r32_5": {"team1_role": "Runner-up Group E", "team2_role": "Runner-up Group I"},
    "r32_6": {"team1_role": "Winner Group I", "team2_allowed_groups": ["C", "D", "F", "G", "H"]},
    "r32_7": {"team1_role": "Winner Group A", "team2_allowed_groups": ["C", "E", "F", "H", "I"]},
    "r32_8": {"team1_role": "Winner Group L", "team2_allowed_groups": ["E", "H", "I", "J", "K"]},
    "r32_9": {"team1_role": "Winner Group G", "team2_allowed_groups": ["A", "E", "H", "I", "J"]},
    "r32_10": {"team1_role": "Winner Group D", "team2_allowed_groups": ["B", "E", "F", "I", "J"]},
    "r32_11": {"team1_role": "Winner Group H", "team2_role": "Runner-up Group J"},
    "r32_12": {"team1_role": "Runner-up Group K", "team2_role": "Runner-up Group L"},
    "r32_13": {"team1_role": "Winner Group B", "team2_allowed_groups": ["E", "F", "G", "I", "J"]},
    "r32_14": {"team1_role": "Runner-up Group D", "team2_role": "Runner-up Group G"},
    "r32_15": {"team1_role": "Winner Group J", "team2_role": "Runner-up Group H"},
    "r32_16": {"team1_role": "Winner Group K", "team2_allowed_groups": ["D", "E", "I", "J", "L"]}
}

MATCH_ID_TO_LABEL = {
    73: "R32-1", 74: "R32-2", 75: "R32-3", 76: "R32-4",
    77: "R32-5", 78: "R32-6", 79: "R32-7", 80: "R32-8",
    81: "R32-9", 82: "R32-10", 83: "R32-13", 84: "R32-14",
    85: "R32-11", 86: "R32-12", 87: "R32-15", 88: "R32-16",
    89: "R16-1", 90: "R16-2", 91: "R16-5", 92: "R16-6",
    93: "R16-3", 94: "R16-4", 95: "R16-7", 96: "R16-8",
    97: "QF-1", 98: "QF-2", 99: "QF-3", 100: "QF-4",
    101: "SF-1", 102: "SF-2",
    104: "SF-1", 103: "SF-1",
}

KNOCKOUT_DEPS = {
    89: {"t1_from": ("winner", 74), "t2_from": ("winner", 77)},
    90: {"t1_from": ("winner", 73), "t2_from": ("winner", 75)},
    91: {"t1_from": ("winner", 76), "t2_from": ("winner", 78)},
    92: {"t1_from": ("winner", 79), "t2_from": ("winner", 80)},
    93: {"t1_from": ("winner", 83), "t2_from": ("winner", 84)},
    94: {"t1_from": ("winner", 81), "t2_from": ("winner", 82)},
    95: {"t1_from": ("winner", 86), "t2_from": ("winner", 88)},
    96: {"t1_from": ("winner", 85), "t2_from": ("winner", 87)},
    97: {"t1_from": ("winner", 89), "t2_from": ("winner", 90)},
    98: {"t1_from": ("winner", 93), "t2_from": ("winner", 94)},
    99: {"t1_from": ("winner", 91), "t2_from": ("winner", 92)},
    100: {"t1_from": ("winner", 95), "t2_from": ("winner", 96)},
    101: {"t1_from": ("winner", 97), "t2_from": ("winner", 98)},
    102: {"t1_from": ("winner", 99), "t2_from": ("winner", 100)},
    103: {"t1_from": ("loser", 101), "t2_from": ("loser", 102)},
    104: {"t1_from": ("winner", 101), "t2_from": ("winner", 102)},
}

R32_SECTOR_IDS = [74, 77, 73, 75, 83, 84, 81, 82, 76, 78, 79, 80, 86, 88, 85, 87]
R16_SECTOR_IDS = [89, 90, 93, 94, 91, 92, 95, 96]
QF_SECTOR_IDS = [97, 98, 99, 100]
SF_SECTOR_IDS = [101, 102]


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


def translate_espn_placeholder(name: str | None) -> str:
    if not name:
        return ""
    name = name.strip()
    m = re.match(r"Group ([A-L]) Winner", name, re.IGNORECASE)
    if m:
        return f"Winner Group {m.group(1).upper()}"
    m = re.match(r"Winner Group ([A-L])", name, re.IGNORECASE)
    if m:
        return f"Winner Group {m.group(1).upper()}"
    m = re.match(r"Group ([A-L]) 2nd Place", name, re.IGNORECASE)
    if m:
        return f"Runner-up Group {m.group(1).upper()}"
    m = re.match(r"Third Place Group ([A-L/]+)", name, re.IGNORECASE)
    if m:
        return f"3rd Group {m.group(1).upper()}"
    m = re.match(r"Round of 32 (\d+) Winner", name, re.IGNORECASE)
    if m:
        return f"Winner Match R32-{m.group(1)}"
    m = re.match(r"Round of 16 (\d+) Winner", name, re.IGNORECASE)
    if m:
        return f"Winner Match R16-{m.group(1)}"
    m = re.match(r"Quarterfinal (\d+) Winner", name, re.IGNORECASE)
    if m:
        return f"Winner Match QF-{m.group(1)}"
    m = re.match(r"Semifinal (\d+) Winner", name, re.IGNORECASE)
    if m:
        return f"Winner Match SF-{m.group(1)}"
    m = re.match(r"Semifinal (\d+) Loser", name, re.IGNORECASE)
    if m:
        return f"Loser Match SF-{m.group(1)}"
    return normalize_team_name(name)


def main() -> None:
    ap = argparse.ArgumentParser(description="Update World Cup standings and bracket from ESPN.")
    ap.add_argument("--season-start", default=SEASON_START, help="YYYYMMDD window start")
    ap.add_argument("--end", default=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d"), help="YYYYMMDD window end")
    ap.add_argument("--write", action="store_true", help="Write updates back to grid_state.json")
    args = ap.parse_args()

    print(f"Loading grid_state from {GRID_STATE}...")
    with open(GRID_STATE, "r", encoding="utf-8") as f:
        grid_state = json.load(f)

    # Gather matches
    print(f"Scanning ESPN scoreboard from {args.season_start} to {args.end}...")
    all_events = []
    end_scan = max(args.end, "20260719")
    for day in _date_range(args.season_start, end_scan):
        try:
            data = _get(f"{ESPN_BASE}/scoreboard?dates={day}")
            all_events.extend(data.get("events", []))
        except Exception:
            continue

    events_by_id = {ev["id"]: ev for ev in all_events}
    events = list(events_by_id.values())
    print(f"Found {len(events)} unique matches.")

    parsed_matches = []
    for ev in events:
        comp = (ev.get("competitions") or [{}])[0]
        status = comp.get("status", {}).get("type", {}).get("state")
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue

        h_name = home.get("team", {}).get("displayName")
        a_name = away.get("team", {}).get("displayName")
        t1 = translate_espn_placeholder(h_name)
        t2 = translate_espn_placeholder(a_name)

        h_score = home.get("score")
        a_score = away.get("score")

        winner = None
        if status == "post":
            if home.get("winner") is True:
                winner = t1
            elif away.get("winner") is True:
                winner = t2

        parsed_matches.append({
            "event_id": ev["id"],
            "team1": t1,
            "team2": t2,
            "score1": int(h_score) if h_score is not None and str(h_score).strip() != "" else None,
            "score2": int(a_score) if a_score is not None and str(a_score).strip() != "" else None,
            "status": status,
            "winner": winner
        })

    # Group standings computation
    print("Computing group standings...")
    team_stats = {}
    team_to_group = {}
    for group in grid_state["groups"]:
        for team_entry in group["standings"]:
            team_name = team_entry["team"]
            team_stats[team_name] = {
                "team": team_name, "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0
            }
            team_to_group[team_name] = group["name"]

    group_matches_processed = 0
    for m in parsed_matches:
        t1 = m["team1"]
        t2 = m["team2"]
        if t1 in team_to_group and t2 in team_to_group and team_to_group[t1] == team_to_group[t2]:
            group_matches_processed += 1
            if m["status"] == "post" and m["score1"] is not None and m["score2"] is not None:
                s1, s2 = m["score1"], m["score2"]
                team_stats[t1]["p"] += 1
                team_stats[t1]["gf"] += s1
                team_stats[t1]["ga"] += s2
                team_stats[t1]["gd"] += (s1 - s2)

                team_stats[t2]["p"] += 1
                team_stats[t2]["gf"] += s2
                team_stats[t2]["ga"] += s1
                team_stats[t2]["gd"] += (s2 - s1)

                if s1 > s2:
                    team_stats[t1]["w"] += 1
                    team_stats[t1]["pts"] += 3
                    team_stats[t2]["l"] += 1
                elif s2 > s1:
                    team_stats[t2]["w"] += 1
                    team_stats[t2]["pts"] += 3
                    team_stats[t1]["l"] += 1
                else:
                    team_stats[t1]["d"] += 1
                    team_stats[t1]["pts"] += 1
                    team_stats[t2]["d"] += 1
                    team_stats[t2]["pts"] += 1

    new_groups = []
    group_ranks = {}
    for group in grid_state["groups"]:
        g_name = group["name"]
        standings = []
        for team_entry in group["standings"]:
            standings.append(team_stats[team_entry["team"]])
        # Sort by FIFA rules: pts, gd, gf descending
        standings.sort(key=lambda x: (x.get("pts", 0), x.get("gd", 0), x.get("gf", 0)), reverse=True)
        new_groups.append({
            "name": g_name,
            "standings": standings
        })

        group_letter = g_name.replace("Group ", "").strip().upper()
        for rank, entry in enumerate(standings, 1):
            group_ranks[entry["team"]] = (rank, group_letter)

    print(f"Processed {group_matches_processed} group matches.")

    # Bracket resolution
    print("Matching knockout matches...")
    def get_team_role(team_str: str) -> str:
        if team_str in group_ranks:
            rank, gl = group_ranks[team_str]
            if rank == 1:
                return f"Winner Group {gl}"
            elif rank == 2:
                return f"Runner-up Group {gl}"
            elif rank == 3:
                return f"3rd Group {gl}"
            else:
                return f"4th Group {gl}"
        return team_str

    db = {}

    # 1. Round of 32 (Matches 73-88)
    r32_mapping = [
        (73, "r32_1"), (74, "r32_2"), (75, "r32_3"), (76, "r32_4"),
        (77, "r32_5"), (78, "r32_6"), (79, "r32_7"), (80, "r32_8"),
        (81, "r32_9"), (82, "r32_10"), (83, "r32_13"), (84, "r32_14"),
        (85, "r32_11"), (86, "r32_12"), (87, "r32_15"), (88, "r32_16")
    ]
    for mid, slot_id in r32_mapping:
        slot_def = R32_SLOT_DEFS[slot_id]
        matched_m = None
        for m in parsed_matches:
            t1, t2 = m["team1"], m["team2"]
            if t1 in team_to_group and t2 in team_to_group and team_to_group[t1] == team_to_group[t2]:
                # Skip group matches
                continue

            role_a = get_team_role(t1)
            role_b = get_team_role(t2)

            t1_role = slot_def.get("team1_role")
            t2_role = slot_def.get("team2_role")
            allowed_groups = slot_def.get("team2_allowed_groups")

            is_match = False
            if t1_role and t2_role:
                if (role_a == t1_role and role_b == t2_role) or (role_b == t1_role and role_a == t2_role):
                    is_match = True
            elif t1_role and allowed_groups:
                if role_a == t1_role and role_b.startswith("3rd Group "):
                    gl = role_b.replace("3rd Group ", "").strip()
                    if gl in allowed_groups:
                        is_match = True
                elif role_b == t1_role and role_a.startswith("3rd Group "):
                    gl = role_a.replace("3rd Group ", "").strip()
                    if gl in allowed_groups:
                        is_match = True

            if is_match:
                matched_m = m
                break

        if matched_m:
            score1 = matched_m["score1"] if matched_m["status"] in ("post", "in") else None
            score2 = matched_m["score2"] if matched_m["status"] in ("post", "in") else None
            winner = matched_m["winner"]
            loser = None
            if winner:
                loser = matched_m["team2"] if winner == matched_m["team1"] else matched_m["team1"]

            db[mid] = {
                "id": slot_id,
                "team1": matched_m["team1"],
                "team2": matched_m["team2"],
                "score1": score1,
                "score2": score2,
                "winner": winner,
                "loser": loser
            }
        else:
            team2_ph = f"3rd Group {'/'.join(slot_def.get('team2_allowed_groups'))}" if slot_def.get("team2_allowed_groups") else slot_def.get("team2_role") or "???"
            db[mid] = {
                "id": slot_id,
                "team1": slot_def.get("team1_role") or "???",
                "team2": team2_ph,
                "score1": None, "score2": None, "winner": None, "loser": None
            }

    # 2. Subsequent matches 89 to 104
    for mid in sorted(KNOCKOUT_DEPS.keys()):
        dep = KNOCKOUT_DEPS[mid]
        t1_type, t1_parent = dep["t1_from"]
        t2_type, t2_parent = dep["t2_from"]

        parent1 = db.get(t1_parent)
        if parent1 and parent1.get(t1_type):
            team1 = parent1[t1_type]
        else:
            team1 = f"{t1_type.capitalize()} Match {MATCH_ID_TO_LABEL[t1_parent]}"

        parent2 = db.get(t2_parent)
        if parent2 and parent2.get(t2_type):
            team2 = parent2[t2_type]
        else:
            team2 = f"{t2_type.capitalize()} Match {MATCH_ID_TO_LABEL[t2_parent]}"

        matched_m = None
        for m in parsed_matches:
            t1, t2 = m["team1"], m["team2"]
            if t1 in team_to_group and t2 in team_to_group and team_to_group[t1] == team_to_group[t2]:
                continue
            if (t1 == team1 and t2 == team2) or (t2 == team1 and t1 == team2):
                matched_m = m
                break

        score1, score2, winner, loser = None, None, None, None
        team1_display, team2_display = team1, team2

        if matched_m:
            score1 = matched_m["score1"] if matched_m["status"] in ("post", "in") else None
            score2 = matched_m["score2"] if matched_m["status"] in ("post", "in") else None
            winner = matched_m["winner"]
            if winner:
                loser = matched_m["team2"] if winner == matched_m["team1"] else matched_m["team1"]
            team1_display = matched_m["team1"]
            team2_display = matched_m["team2"]
        else:
            for m in parsed_matches:
                t1, t2 = m["team1"], m["team2"]
                if (t1 == team1 and t2 == team2) or (t2 == team1 and t1 == team2):
                    matched_m = m
                    break
            if matched_m:
                score1 = matched_m["score1"] if matched_m["status"] in ("post", "in") else None
                score2 = matched_m["score2"] if matched_m["status"] in ("post", "in") else None
                team1_display = matched_m["team1"]
                team2_display = matched_m["team2"]

        db[mid] = {
            "id": f"r16_{mid}" if 89 <= mid <= 96 else f"qf_{mid}" if 97 <= mid <= 100 else f"sf_{mid}" if 101 <= mid <= 102 else "f_104" if mid == 104 else "tp_1",
            "team1": team1_display,
            "team2": team2_display,
            "score1": score1,
            "score2": score2,
            "winner": winner,
            "loser": loser
        }

    # Build rounds and third_place nested structures for grid_state fallback
    new_rounds = []
    # Round of 32
    r32_matches = []
    for slot_id in [f"r32_{i}" for i in range(1, 17)]:
        mid = next(k for k, v in db.items() if v["id"] == slot_id)
        r32_matches.append({
            "id": slot_id, "team1": db[mid]["team1"], "team2": db[mid]["team2"],
            "score1": db[mid]["score1"], "score2": db[mid]["score2"], "winner": db[mid]["winner"]
        })
    new_rounds.append({"name": "Round of 32", "matches": r32_matches})

    # Round of 16
    r16_matches = []
    for mid in R16_SECTOR_IDS:
        r16_matches.append({
            "id": f"r16_{mid}", "team1": db[mid]["team1"], "team2": db[mid]["team2"],
            "score1": db[mid]["score1"], "score2": db[mid]["score2"], "winner": db[mid]["winner"]
        })
    new_rounds.append({"name": "Round of 16", "matches": r16_matches})

    # Quarterfinals
    qf_matches = []
    for mid in QF_SECTOR_IDS:
        qf_matches.append({
            "id": f"qf_{mid}", "team1": db[mid]["team1"], "team2": db[mid]["team2"],
            "score1": db[mid]["score1"], "score2": db[mid]["score2"], "winner": db[mid]["winner"]
        })
    new_rounds.append({"name": "Quarterfinals", "matches": qf_matches})

    # Semifinals
    sf_matches = []
    for mid in SF_SECTOR_IDS:
        sf_matches.append({
            "id": f"sf_{mid}", "team1": db[mid]["team1"], "team2": db[mid]["team2"],
            "score1": db[mid]["score1"], "score2": db[mid]["score2"], "winner": db[mid]["winner"]
        })
    new_rounds.append({"name": "Semifinals", "matches": sf_matches})

    # Final
    final_matches = [{
        "id": "f_1", "team1": db[104]["team1"], "team2": db[104]["team2"],
        "score1": db[104]["score1"], "score2": db[104]["score2"], "winner": db[104]["winner"]
    }]
    new_rounds.append({"name": "Final", "matches": final_matches})

    new_third_place = {
        "id": "tp_1", "team1": db[103]["team1"], "team2": db[103]["team2"],
        "score1": db[103]["score1"], "score2": db[103]["score2"], "winner": db[103]["winner"]
    }

    # Build flat structures for frontend preference
    def get_flat_list(mids: list[int], prefix: str) -> list[dict]:
        return [{
            "id": f"{prefix}_{mid}", "team1": db[mid]["team1"], "team2": db[mid]["team2"],
            "score1": db[mid]["score1"], "score2": db[mid]["score2"], "winner": db[mid]["winner"]
        } for mid in mids]

    flat_r32 = get_flat_list(R32_SECTOR_IDS, "r32")
    flat_r16 = get_flat_list(R16_SECTOR_IDS, "r16")
    flat_qf = get_flat_list(QF_SECTOR_IDS, "qf")
    flat_sf = get_flat_list(SF_SECTOR_IDS, "sf")
    flat_final = get_flat_list([104], "final")
    flat_third = get_flat_list([103], "third")

    print("\nStandings summary:")
    for group in new_groups[:3]:
        print(f"  {group['name']}: {', '.join(t['team'] for t in group['standings'])}")

    print("\nBracket matchups check:")
    for mid in [73, 74, 89, 97, 104]:
        label = MATCH_ID_TO_LABEL.get(mid, str(mid))
        m = db[mid]
        print(f"  Match {mid} ({label}): {m['team1']} vs {m['team2']} -> Winner: {m['winner']}")

    if not args.write:
        print("\n(dry-run; pass --write to update grid_state.json)")
        return

    # Surgical write
    print(f"\nWriting updates to {GRID_STATE}...")
    grid_state["groups"] = new_groups
    grid_state["rounds"] = new_rounds
    grid_state["third_place"] = new_third_place
    grid_state["r32"] = flat_r32
    grid_state["r16"] = flat_r16
    grid_state["qf"] = flat_qf
    grid_state["sf"] = flat_sf
    grid_state["final"] = flat_final
    grid_state["third"] = flat_third

    with open(GRID_STATE, "w", encoding="utf-8") as f:
        json.dump(grid_state, f, indent=2, ensure_ascii=False)

    print("Success! Standings and bracket updated.")


if __name__ == "__main__":
    main()
