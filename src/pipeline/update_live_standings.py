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
    Simulated live aggregator. In a production pipeline, this would hit 
    an API (or scrape Sofascore/FBref) to collect current GD and Pts for all 12 groups.
    """
    # Current active standings as of June 14, 2026
    return [
        {
            "name": "Group A",
            "standings": [
                {"team": "Mexico", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 2, "pts": 3},
                {"team": "Czechia", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "South Korea", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "South Africa", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -2, "pts": 0}
            ]
        },
        {
            "name": "Group B",
            "standings": [
                {"team": "Canada", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Bosnia and Herzegovina", "p": 1, "w": 0, "d": 1, "l": 0, "gd": 0, "pts": 1},
                {"team": "Qatar", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Switzerland", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0}
            ]
        },
        {
            "name": "Group C",
            "standings": [
                {"team": "Brazil", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 1, "pts": 3},
                {"team": "Haiti", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Scotland", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Morocco", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0}
            ]
        },
        {
            "name": "Group D",
            "standings": [
                {"team": "United States", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 2, "pts": 3},
                {"team": "Australia", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Turkiye", "p": 0, "w": 0, "d": 0, "l": 0, "gd": 0, "pts": 0},
                {"team": "Paraguay", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -2, "pts": 0}
            ]
        },
        {
            "name": "Group E",
            "standings": [
                {"team": "Germany", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 2, "pts": 3},
                {"team": "Ecuador", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 1, "pts": 3},
                {"team": "Ivory Coast", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0},
                {"team": "Curacao", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -2, "pts": 0}
            ]
        },
        {
            "name": "Group F",
            "standings": [
                {"team": "Netherlands", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 1, "pts": 3},
                {"team": "Sweden", "p": 1, "w": 1, "d": 0, "l": 0, "gd": 1, "pts": 3},
                {"team": "Japan", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0},
                {"team": "Tunisia", "p": 1, "w": 0, "d": 0, "l": 1, "gd": -1, "pts": 0}
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
