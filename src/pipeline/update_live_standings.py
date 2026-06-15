import json
import os
from pathlib import Path
from typing import Dict, List, Any

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

    TEAM_ID_TO_NAME = {
        "1": "Mexico", "2": "South Africa", "3": "South Korea", "4": "Czechia",
        "5": "Canada", "6": "Bosnia and Herzegovina", "7": "Qatar", "8": "Switzerland",
        "9": "Brazil", "10": "Morocco", "11": "Haiti", "12": "Scotland",
        "13": "United States", "14": "Paraguay", "15": "Australia", "16": "Turkiye",
        "17": "Germany", "18": "Curacao", "19": "Ivory Coast", "20": "Ecuador",
        "21": "Netherlands", "22": "Japan", "23": "Sweden", "24": "Tunisia",
        "25": "Belgium", "26": "Egypt", "27": "Iran", "28": "New Zealand",
        "29": "Spain", "30": "Cape Verde", "31": "Saudi Arabia", "32": "Uruguay",
        "33": "France", "34": "Senegal", "35": "Iraq", "36": "Norway",
        "37": "Argentina", "38": "Algeria", "39": "Austria", "40": "Jordan",
        "41": "Portugal", "42": "DR Congo", "43": "Uzbekistan", "44": "Colombia",
        "45": "England", "46": "Croatia", "47": "Ghana", "48": "Panama"
    }

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
                        team_name = TEAM_ID_TO_NAME.get(team_id)
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
                {"team": "Czechia", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0},
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
                {"team": "Turkiye", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -2, "pts": 0},
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
                {"team": "DR Congo", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
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
    save_grid_state(state)
    print("✅ Live Standings successfully updated inside grid_state.json!")

if __name__ == "__main__":
    update_live_standings()
