import json
import os
from pathlib import Path
from typing import Dict, List, Any

from src.common.team_identity import normalize_team_name, team_id_to_name

GRID_STATE_PATH = Path("./data/bracket/grid_state.json")

def load_grid_state() -> Dict[str, Any]:
    if not GRID_STATE_PATH.exists():
        raise FileNotFoundError(f"grid_state.json not found at {GRID_STATE_PATH}")
    with open(GRID_STATE_PATH, "r") as f:
        return json.load(f)

def save_grid_state(data: Dict[str, Any]):
    os.makedirs(GRID_STATE_PATH.parent, exist_ok=True)
    with open(GRID_STATE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def fetch_live_group_standings() -> List[Dict[str, Any]]:
    """
    Fetches live standings from the 2026 World Cup API.
    If the API call fails, falls back to a curated set of standings as of June 14, 2026.
    """
    import subprocess

    try:
        url = "https://worldcup26.ir/get/groups"
        result = subprocess.run(['curl', '-s', '-k', url], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            api_data = json.loads(result.stdout)
            groups_list = []
            if isinstance(api_data, dict) and "groups" in api_data:
                groups_list = api_data["groups"]
            elif isinstance(api_data, list):
                groups_list = api_data
                
            if groups_list:
                groups = []
                for group in groups_list:
                    group_name = f"Group {group.get('name', '')}"
                    standings = []
                    for t in group.get("teams", []):
                        team_id = str(t.get("team_id", ""))
                        team_name = team_id_to_name(team_id)
                        if team_name:
                            standings.append({
                                "team": team_name,
                                "p": int(t.get("mp", 0)),
                                "w": int(t.get("w", 0)),
                                "d": int(t.get("d", 0)),
                                "l": int(t.get("l", 0)),
                                "gf": int(t.get("gf", 0)),
                                "ga": int(t.get("ga", 0)),
                                "gd": int(t.get("gd", 0)),
                                "pts": int(t.get("pts", 0))
                            })
                    # Sort standings by pts, then gd, then gf descending
                    standings.sort(key=lambda x: (x.get("pts", 0), x.get("gd", 0), x.get("gf", 0)), reverse=True)
                    groups.append({
                        "name": group_name,
                        "standings": standings
                    })
                print("✅ Successfully fetched live group standings from 2026 World Cup API!")
                return groups
    except Exception as e:
        print(f"⚠️ Live API call failed, using offline fallback. Error: {e}")

    # Offline fallback (correct as of June 14, 2026)
    return [
        {
            "name": "Group A",
            "standings": [
                {"team": "Mexico", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 2, "pts": 3},
                {"team": "South Korea", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 1, "pts": 3},
                {"team": "Czech Republic", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0},
                {"team": "South Africa", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -2, "pts": 0}
            ]
        },
        {
            "name": "Group B",
            "standings": [
                {"team": "Canada", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Bosnia and Herzegovina", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Qatar", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Switzerland", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1}
            ]
        },
        {
            "name": "Group C",
            "standings": [
                {"team": "Scotland", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 1, "pts": 3},
                {"team": "Brazil", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Morocco", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Haiti", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0}
            ]
        },
        {
            "name": "Group D",
            "standings": [
                {"team": "United States", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 3, "pts": 3},
                {"team": "Australia", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 2, "pts": 3},
                {"team": "Turkey", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -2, "pts": 0},
                {"team": "Paraguay", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -3, "pts": 0}
            ]
        },
        {
            "name": "Group E",
            "standings": [
                {"team": "Germany", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 6, "pts": 3},
                {"team": "Ivory Coast", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 1, "pts": 3},
                {"team": "Ecuador", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0},
                {"team": "Curacao", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -6, "pts": 0}
            ]
        },
        {
            "name": "Group F",
            "standings": [
                {"team": "Sweden", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 4, "pts": 3},
                {"team": "Netherlands", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Japan", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Tunisia", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -4, "pts": 0}
            ]
        },
        {
            "name": "Group G",
            "standings": [
                {"team": "Belgium", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Egypt", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Iran", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "New Zealand", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0}
            ]
        },
        {
            "name": "Group H",
            "standings": [
                {"team": "Cape Verde", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Saudi Arabia", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Spain", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Uruguay", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0}
            ]
        },
        {
            "name": "Group I",
            "standings": [
                {"team": "France", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Iraq", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Norway", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Senegal", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0}
            ]
        },
        {
            "name": "Group J",
            "standings": [
                {"team": "Algeria", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Argentina", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Austria", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Jordan", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0}
            ]
        },
        {
            "name": "Group K",
            "standings": [
                {"team": "Colombia", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Democratic Republic of the Congo", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Portugal", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Uzbekistan", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0}
            ]
        },
        {
            "name": "Group L",
            "standings": [
                {"team": "Croatia", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "England", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Ghana", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Panama", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0}
            ]
        }
    ]

def update_live_standings():
    print("🔄 Running World Cup 2026 Live Standings Update...")
    state = load_grid_state()
    live_groups = fetch_live_group_standings()
    state["groups"] = live_groups
    
    # Fetch live games to apply corrections
    import subprocess
    try:
        url = "https://worldcup26.ir/get/games"
        result = subprocess.run(['curl', '-s', '-k', url], capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            api_games_data = json.loads(result.stdout)
            games_list = api_games_data.get("games", []) if isinstance(api_games_data, dict) else api_games_data
            
            if games_list:
                print("🔄 Correcting standings using finished games list...")
                team_stats = {}
                for group_obj in state.get("groups", []):
                    for team_obj in group_obj.get("standings", []):
                        t_name = team_obj["team"]
                        team_stats[t_name] = {
                            "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0
                        }
                
                for game in games_list:
                    if game.get("type") == "group" and (game.get("finished") == "TRUE" or game.get("finished") is True):
                        h = game.get("home_team_name_en") or game.get("home_team_label") or ""
                        a = game.get("away_team_name_en") or game.get("away_team_label") or ""
                        
                        h = normalize_team_name(h)
                        a = normalize_team_name(a)
                        
                        if h in team_stats and a in team_stats:
                            try:
                                h_score = int(game.get("home_score", 0))
                                a_score = int(game.get("away_score", 0))
                            except Exception:
                                continue
                                
                            team_stats[h]["p"] += 1
                            team_stats[h]["gf"] += h_score
                            team_stats[h]["ga"] += a_score
                            team_stats[h]["gd"] += (h_score - a_score)
                            
                            team_stats[a]["p"] += 1
                            team_stats[a]["gf"] += a_score
                            team_stats[a]["ga"] += h_score
                            team_stats[a]["gd"] += (a_score - h_score)
                            
                            if h_score > a_score:
                                team_stats[h]["w"] += 1
                                team_stats[h]["pts"] += 3
                                team_stats[a]["l"] += 1
                            elif a_score > h_score:
                                team_stats[a]["w"] += 1
                                team_stats[a]["pts"] += 3
                                team_stats[h]["l"] += 1
                            else:
                                team_stats[h]["d"] += 1
                                team_stats[h]["pts"] += 1
                                team_stats[a]["d"] += 1
                                team_stats[a]["pts"] += 1
                                
                corrected_groups = []
                for group_obj in state.get("groups", []):
                    corrected_standings = []
                    for team_obj in group_obj.get("standings", []):
                        t_name = team_obj["team"]
                        stats = team_stats.get(t_name)
                        if stats:
                            corrected_standings.append({
                                "team": t_name,
                                "p": stats["p"],
                                "w": stats["w"],
                                "d": stats["d"],
                                "l": stats["l"],
                                "gf": stats["gf"],
                                "ga": stats["ga"],
                                "gd": stats["gd"],
                                "pts": stats["pts"]
                            })
                        else:
                            corrected_standings.append(team_obj)
                    
                    corrected_standings.sort(key=lambda x: (x.get("pts", 0), x.get("gd", 0), x.get("gf", 0)), reverse=True)
                    corrected_groups.append({
                        "name": group_obj["name"],
                        "standings": corrected_standings
                    })
                state["groups"] = corrected_groups
    except Exception as e:
        print(f"⚠️ Standings correction failed: {e}")
        
    save_grid_state(state)
    print("✅ Live Standings successfully updated inside grid_state.json!")

if __name__ == "__main__":
    update_live_standings()
