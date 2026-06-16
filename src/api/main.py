import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

# 1. Path setups
API_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_DIR.parents[1]

sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "src" / "analytics"))

from google.cloud import bigquery
from src.analytics.soccerdata_client import SoccerDataClient, get_dixon_coles_prediction
from src.analytics.fifa_visualizations_bq import (
    get_cached_shot_map,
    get_cached_pass_network,
    get_cached_touch_heatmap,
    get_cached_attacking_passes,
    get_cached_radar_chart,
    get_cached_progressive_actions_map
)
from src.analytics.fifa_metrics_bq import get_match_radar_stats

# Initialize FastAPI App
app = FastAPI(title="FIFA World Cup 2026 Analytics API", description="REST API for match forecasts, team comparisons, and event visualizations.")

# Enable CORS for static site hosting (like accionar.xyz or localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = PROJECT_ROOT / "data"

# Memory cache for standings
_standings_cache = {}

def clean_team_name(name: str) -> str:
    return (name.lower()
            .strip()
            .replace(" ", "_")
            .replace("'", "")
            .replace("ô", "o")
            .replace("é", "e")
            .replace("ö", "o")
            .replace("ç", "c")
            .replace("í", "i")
            .replace("á", "a")
            .replace("ú", "u"))

def load_live_bracket_state() -> dict:
    bracket_path = DATA_DIR / "bracket" / "grid_state.json"
    if not bracket_path.exists():
        return {}

    with open(bracket_path, "r", encoding="utf-8") as f:
        data = json.load(f)

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

    # 1. Fetch live group standings
    try:
        url_groups = "https://worldcup26.ir/get/groups"
        result_groups = subprocess.run(['curl', '-s', '-k', url_groups], capture_output=True, text=True, timeout=5)
        if result_groups.returncode == 0:
            api_data = json.loads(result_groups.stdout)
            groups_list = api_data.get("groups", []) if isinstance(api_data, dict) else api_data
                
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
                    standings.sort(key=lambda x: (x.get("pts", 0), x.get("gd", 0), x.get("gf", 0)), reverse=True)
                    groups.append({
                        "name": group_name,
                        "standings": standings
                    })
                data["groups"] = groups
    except Exception:
        pass

    # 2. Fetch live games and dynamically build knockout rounds
    try:
        url_games = "https://worldcup26.ir/get/games"
        result_games = subprocess.run(['curl', '-s', '-k', url_games], capture_output=True, text=True, timeout=5)
        if result_games.returncode == 0:
            api_games_data = json.loads(result_games.stdout)
            games_list = api_games_data.get("games", []) if isinstance(api_games_data, dict) else api_games_data
                
            if games_list:
                # Standings corrections
                try:
                    MAP_TEAMS = {
                        "Turkey": "Turkiye",
                        "Czech Republic": "Czechia",
                        "Curaçao": "Curacao",
                        "Democratic Republic of the Congo": "DR Congo",
                        "Côte d'Ivoire": "Ivory Coast",
                        "Cote d'Ivoire": "Ivory Coast"
                    }
                    
                    team_stats = {}
                    for group_obj in data.get("groups", []):
                        for team_obj in group_obj.get("standings", []):
                            t_name = team_obj["team"]
                            team_stats[t_name] = {
                                "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0
                            }
                    
                    for game in games_list:
                        if game.get("type") == "group" and (game.get("finished") == "TRUE" or game.get("finished") is True):
                            h = game.get("home_team_name_en") or game.get("home_team_label") or ""
                            a = game.get("away_team_name_en") or game.get("away_team_label") or ""
                            h = MAP_TEAMS.get(h, h)
                            a = MAP_TEAMS.get(a, a)
                            
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
                    for group_obj in data.get("groups", []):
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
                    data["groups"] = corrected_groups
                except Exception:
                    pass
                
                game_map = {str(g.get("id")): g for g in games_list}
                r32_ids = ["74", "77", "73", "75", "83", "84", "81", "82", "76", "78", "79", "80", "86", "88", "85", "87"]
                r16_ids = ["89", "90", "93", "94", "91", "92", "95", "96"]
                qf_ids = ["97", "98", "99", "100"]
                sf_ids = ["101", "102"]
                final_id = "104"
                third_id = "103"
                
                def make_match(match_id, prefix):
                    g = game_map.get(match_id)
                    if not g:
                        return {"id": f"{prefix}_{match_id}", "team1": "???", "team2": "???", "score1": None, "score2": None, "winner": None}
                    
                    t1 = g.get("home_team_name_en") or g.get("home_team_label") or "???"
                    t2 = g.get("away_team_name_en") or g.get("away_team_label") or "???"
                    TEAM_NAME_MAP = {
                        "Turkey": "Turkiye",
                        "Czech Republic": "Czechia",
                        "Curaçao": "Curacao",
                        "Democratic Republic of the Congo": "DR Congo"
                    }
                    t1 = TEAM_NAME_MAP.get(t1, t1)
                    t2 = TEAM_NAME_MAP.get(t2, t2)
                    
                    s1 = g.get("home_score")
                    s2 = g.get("away_score")
                    winner_id = g.get("winner")
                    winner_name = None
                    if winner_id:
                        winner_name = TEAM_ID_TO_NAME.get(str(winner_id))
                        
                    return {
                        "id": f"{prefix}_{match_id}",
                        "team1": t1,
                        "team2": t2,
                        "score1": int(s1) if s1 is not None and str(s1).strip() != "" else None,
                        "score2": int(s2) if s2 is not None and str(s2).strip() != "" else None,
                        "winner": winner_name
                    }

                data["r32"] = [make_match(mid, "r32") for mid in r32_ids]
                data["r16"] = [make_match(mid, "r16") for mid in r16_ids]
                data["qf"] = [make_match(mid, "qf") for mid in qf_ids]
                data["sf"] = [make_match(mid, "sf") for mid in sf_ids]
                data["final"] = [make_match(final_id, "final")]
                data["third"] = [make_match(third_id, "third")]
    except Exception:
        pass

    return data

MATCH_VISUALIZATION_PROXIES = {
    "Netherlands": {"match_id": 3930180, "team": "Netherlands", "label": "UEFA Euro 2024"},
    "Japan": {"match_id": 3857255, "team": "Japan", "label": "FIFA World Cup 2022"},
    "Ivory Coast": {"match_id": 3922838, "team": "Côte d'Ivoire", "label": "Africa Cup of Nations 2023"},
    "Ecuador": {"match_id": 3939980, "team": "Ecuador", "label": "Copa América 2024"},
    "Sweden": {"match_id": 3788750, "team": "Sweden", "label": "UEFA Euro 2020"},
    "Tunisia": {"match_id": 3920404, "team": "Tunisia", "label": "Africa Cup of Nations 2023"},
    "France": {"match_id": 3930173, "team": "France", "label": "UEFA Euro 2024"},
    "Senegal": {"match_id": 3920412, "team": "Senegal", "label": "Africa Cup of Nations 2023"},
    "Argentina": {"match_id": 3942785, "team": "Argentina", "label": "Copa América 2024"},
    "Algeria": {"match_id": 3920390, "team": "Algeria", "label": "Africa Cup of Nations 2023"},
    "Austria": {"match_id": 3930180, "team": "Austria", "label": "UEFA Euro 2024"},
    "Norway": {"match_id": 3788750, "team": "Sweden", "label": "UEFA Euro 2020 (Proxy)"},
    "Iraq": {"match_id": 3920404, "team": "Tunisia", "label": "Arab Cup 2021 (Proxy)"},
    "Jordan": {"match_id": 3920404, "team": "Tunisia", "label": "Arab Cup 2021 (Proxy)"}
}

# --- REST ENDPOINTS ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/schedule")
def get_schedule():
    matches_dir = DATA_DIR / "matches"
    matches_details = []
    if matches_dir.exists():
        for folder in sorted(matches_dir.iterdir()):
            if folder.is_dir() and folder.name.endswith("_2026"):
                sum_path = folder / "summary.json"
                if sum_path.exists():
                    try:
                        with open(sum_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        meta = data.get("metadata", {})
                        matches_details.append({
                            "id": folder.name,
                            "team1": meta.get("team1"),
                            "team2": meta.get("team2"),
                            "date": meta.get("date"),
                            "time": meta.get("time"),
                            "venue": meta.get("venue"),
                            "stage": meta.get("stage")
                        })
                    except Exception:
                        pass
    return {"matches": matches_details}

@app.get("/api/match/{match_id}/summary")
def get_match_summary(match_id: str):
    sum_path = DATA_DIR / "matches" / match_id / "summary.json"
    if not sum_path.exists():
        raise HTTPException(status_code=404, detail="Summary payload not found")
    with open(sum_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/match/{match_id}/metrics")
def get_match_metrics(match_id: str):
    met_path = DATA_DIR / "matches" / match_id / "metrics.json"
    if not met_path.exists():
        raise HTTPException(status_code=404, detail="Metrics payload not found")
    with open(met_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/standings")
def get_standings():
    return load_live_bracket_state()

@app.get("/api/forecast")
def get_forecast(team1: str, team2: str):
    sd_client = SoccerDataClient()
    elo_t1 = sd_client.fetch_club_elo_ratings(team1).get("elo_rating") if sd_client.fetch_club_elo_ratings(team1) else None
    elo_t2 = sd_client.fetch_club_elo_ratings(team2).get("elo_rating") if sd_client.fetch_club_elo_ratings(team2) else None
    
    if elo_t1 is not None and elo_t2 is not None:
        dc_res = get_dixon_coles_prediction(elo_t1, elo_t2) or {}
        return dc_res
    return {
        "team1_win": None, "draw": None, "team2_win": None, "confidence": None, "score_probabilities": []
    }

# --- Event Visualizations serving binary images ---

@app.get("/api/visualizations/{match_id}/{viz_type}")
def get_visualization(match_id: str, viz_type: str, team: str = None):
    parts = match_id.replace("_2026", "").split("_")
    t1_key = parts[0]
    t2_key = parts[1] if len(parts) > 1 else ""

    team_mapping = {
        "france": "France", "senegal": "Senegal",
        "iraq": "Iraq", "norway": "Norway",
        "argentina": "Argentina", "algeria": "Algeria",
        "austria": "Austria", "jordan": "Jordan",
        "portugal": "Portugal", "democratic_republic_of_the_congo": "DR Congo",
        "england": "England", "croatia": "Croatia",
        "ghana": "Ghana", "panama": "Panama",
        "uzbekistan": "Uzbekistan", "colombia": "Colombia",
        "spain": "Spain", "cape_verde": "Cape Verde",
        "belgium": "Belgium", "egypt": "Egypt",
        "saudi_arabia": "Saudi Arabia", "uruguay": "Uruguay",
        "iran": "Iran", "new_zealand": "New Zealand"
    }

    t1_name = team_mapping.get(t1_key, t1_key.capitalize())
    t2_name = team_mapping.get(t2_key, t2_key.capitalize())

    active_team = t1_name if team is None or clean_team_name(team) == t1_key else t2_name
    proxy = MATCH_VISUALIZATION_PROXIES.get(active_team)

    client = bigquery.Client()
    img_bytes = None

    try:
        if viz_type == "passing_network":
            if proxy:
                img_bytes = get_cached_pass_network(client, proxy["team"], match_id=proxy["match_id"])
        elif viz_type == "shot_map":
            if proxy:
                img_bytes = get_cached_shot_map(client, proxy["team"], match_id=proxy["match_id"])
        elif viz_type == "touch_heatmap":
            if proxy:
                img_bytes = get_cached_touch_heatmap(client, proxy["team"], match_id=proxy["match_id"])
        elif viz_type == "attacking_passes":
            if proxy:
                img_bytes = get_cached_attacking_passes(client, proxy["team"], match_id=proxy["match_id"])
        elif viz_type == "progressive_actions":
            if proxy:
                color = '#00c6ff' if active_team == t1_name else '#ff007f'
                img_bytes = get_cached_progressive_actions_map(client, proxy["match_id"], proxy["team"], color, '#ffffff')
        elif viz_type == "radar_chart":
            proxy1 = MATCH_VISUALIZATION_PROXIES.get(t1_name)
            proxy2 = MATCH_VISUALIZATION_PROXIES.get(t2_name)
            if proxy1 and proxy2:
                t1_vals = get_match_radar_stats(client, proxy1["match_id"], proxy1["team"])
                t2_vals = get_match_radar_stats(client, proxy2["match_id"], proxy2["team"])
                params = ["xG", "Shots", "Passing%", "Tackles", "Pressure%", "Box Entries"]
                low = [0.0, 0.0, 50.0, 0.0, 10.0, 0.0]
                high = [3.0, 20.0, 95.0, 25.0, 40.0, 15.0]

                t1_metrics = [
                    t1_vals.get("xg", 1.2), t1_vals.get("shots", 10.0), t1_vals.get("pass_completion", 80.0),
                    t1_vals.get("tackles", 12.0), t1_vals.get("pressure_regain_pct", 22.0), t1_vals.get("box_entries", 6.0)
                ]
                t2_metrics = [
                    t2_vals.get("xg", 1.0), t2_vals.get("shots", 8.0), t2_vals.get("pass_completion", 78.0),
                    t2_vals.get("tackles", 14.0), t2_vals.get("pressure_regain_pct", 25.0), t2_vals.get("box_entries", 5.0)
                ]
                
                vals = t1_metrics if active_team == t1_name else t2_metrics
                color = '#00c6ff' if active_team == t1_name else '#ff007f'
                img_bytes = get_cached_radar_chart(client, proxy["match_id"], proxy["team"], color, params, low, high, vals)

        if img_bytes:
            return Response(content=img_bytes, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Visualization proxy not found for this team combination")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate visualization plot: {e}")


# Serve static files from the React frontend build
static_dir = API_DIR / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
