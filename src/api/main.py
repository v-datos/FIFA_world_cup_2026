import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
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
    get_cached_progressive_actions_map,
    get_cached_xg_distribution
)
from src.analytics.fifa_metrics_bq import get_match_radar_stats
from src.common.team_identity import (
    canonical_team_slug,
    normalize_team_name,
    team_id_to_name,
    teams_from_match_id,
)

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
    return canonical_team_slug(name)


def parse_schedule_datetime(date_value: str | None, time_value: str | None) -> Optional[datetime]:
    if not date_value:
        return None
    time_text = (time_value or "00:00").strip()
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(f"{date_value.strip()} {time_text}", fmt)
        except ValueError:
            pass
    return None


def parse_live_game_datetime(game: dict) -> Optional[datetime]:
    local_date = str(game.get("local_date") or "").strip()
    if local_date:
        for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S"):
            try:
                return datetime.strptime(local_date, fmt)
            except ValueError:
                pass
    return parse_schedule_datetime(game.get("date"), game.get("time"))


def is_finished_game(game: dict | None) -> bool:
    if not game:
        return False
    value = game.get("finished")
    return value is True or str(value).upper() == "TRUE"


def fetch_live_games_for_schedule() -> tuple[dict[str, dict], str]:
    errors = []
    payload = None
    source = "live_schedule"

    try:
        result = subprocess.run(
            ["curl", "-s", "-k", "--max-time", "10", "https://worldcup26.ir/get/games"],
            capture_output=True,
            text=True,
            timeout=12,
        )
        if result.returncode == 0 and result.stdout.strip():
            payload = json.loads(result.stdout)
        else:
            errors.append(f"live API curl exit {result.returncode}")
    except Exception as exc:
        errors.append(f"live API failed: {exc}")

    if payload is None:
        cache_path = Path("/tmp/games.json")
        try:
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                source = "cache"
        except Exception as exc:
            errors.append(f"cache failed: {exc}")

    games = []
    if isinstance(payload, dict):
        games = payload.get("games", [])
    elif isinstance(payload, list):
        games = payload

    index = {}
    for game in games:
        if not isinstance(game, dict):
            continue
        team1 = normalize_team_name(
            game.get("home_team_name_en")
            or game.get("home_team_label")
            or team_id_to_name(game.get("home_team_id"))
            or ""
        )
        team2 = normalize_team_name(
            game.get("away_team_name_en")
            or game.get("away_team_label")
            or team_id_to_name(game.get("away_team_id"))
            or ""
        )
        if not team1 or not team2:
            continue
        match_id = f"{canonical_team_slug(team1)}_{canonical_team_slug(team2)}_2026"
        index[match_id] = game

    return index, source if index else ("unavailable" if errors else source)


def schedule_lifecycle(
    meta: dict,
    live_game: dict | None,
    now_value: datetime,
    next_24h_end: datetime,
) -> dict:
    kickoff = parse_live_game_datetime(live_game) if live_game else parse_schedule_datetime(meta.get("date"), meta.get("time"))
    kickoff_date = kickoff.date() if kickoff else None
    today = now_value.date()
    is_finished = is_finished_game(live_game)
    if not is_finished and kickoff_date and kickoff_date < today:
        is_finished = True
    live_team1 = live_game.get("home_team_name_en") or live_game.get("home_team_label") if live_game else ""
    live_team2 = live_game.get("away_team_name_en") or live_game.get("away_team_label") if live_game else ""
    unresolved = any(
        token in str(value).lower()
        for value in (live_team1, live_team2)
        for token in ("winner", "runner-up", "runner up", "loser", "???", "tbd")
    )

    if unresolved:
        lifecycle = "unresolved"
    elif is_finished:
        lifecycle = "finished"
    elif kickoff_date == today:
        lifecycle = "today"
    elif kickoff and kickoff > now_value:
        lifecycle = "upcoming"
    else:
        lifecycle = "archived"

    is_upcoming_24h = bool(kickoff and not is_finished and now_value <= kickoff <= next_24h_end)
    return {
        "lifecycle": lifecycle,
        "source_status": "finished" if is_finished else "not_finished" if live_game else "unknown",
        "source_game_id": str(live_game.get("id")) if live_game else None,
        "is_finished": is_finished,
        "is_today": lifecycle == "today",
        "is_upcoming_24h": is_upcoming_24h,
        "is_briefing_candidate": lifecycle == "today" or is_upcoming_24h,
    }

def load_live_bracket_state() -> dict:
    bracket_path = DATA_DIR / "bracket" / "grid_state.json"
    if not bracket_path.exists():
        return {}

    with open(bracket_path, "r", encoding="utf-8") as f:
        data = json.load(f)

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
                    t1 = normalize_team_name(t1)
                    t2 = normalize_team_name(t2)
                    
                    s1 = g.get("home_score")
                    s2 = g.get("away_score")
                    winner_id = g.get("winner")
                    winner_name = None
                    if winner_id:
                        winner_name = team_id_to_name(winner_id)
                        
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

DEFAULT_FORECAST = {
    "team1_win": 0.40,
    "draw": 0.30,
    "team2_win": 0.30,
    "confidence": 0.70,
}

REQUIRED_TEAM_METRIC_FIELDS = [
    "squad_market_value_m",
    "average_age",
    "possession_avg",
    "pass_completion_pct",
    "expected_goals_per_90",
    "expected_goals_conceded_per_90",
    "shots_per_90",
    "ppda",
    "field_tilt_pct",
    "goals_per_90",
    "goals_conceded_per_90",
    "shots_on_target_pct",
    "passes_per_90",
    "xg_per_shot",
    "shots_against_per_90",
]

RADAR_METRIC_FIELDS = [
    "expected_goals_per_90",
    "shots_per_90",
    "pass_completion_pct",
    "possession_avg",
    "ppda",
    "expected_goals_conceded_per_90",
]


def load_match_team_names(match_id: str) -> tuple[Optional[str], Optional[str]]:
    sum_path = DATA_DIR / "matches" / match_id / "summary.json"
    if sum_path.exists():
        try:
            with open(sum_path, "r", encoding="utf-8") as f:
                sum_data = json.load(f)
            return (
                normalize_team_name(sum_data["metadata"]["team1"]),
                normalize_team_name(sum_data["metadata"]["team2"]),
            )
        except Exception:
            pass
    return teams_from_match_id(match_id)


def get_visualization_proxy(team_name: str) -> Optional[dict]:
    return MATCH_VISUALIZATION_PROXIES.get(normalize_team_name(team_name))


def _number_or_none(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def is_default_forecast(forecast: dict) -> bool:
    if not forecast:
        return True
    for key, expected in DEFAULT_FORECAST.items():
        actual = _number_or_none(forecast.get(key))
        if actual is None or abs(actual - expected) > 0.0001:
            return False
    return True


def build_team_metric_quality(metrics: dict, team: str) -> dict:
    team_metrics = metrics.get(team) or {}
    present_fields = [
        field for field in REQUIRED_TEAM_METRIC_FIELDS
        if _number_or_none(team_metrics.get(field)) is not None
    ]
    missing_fields = [
        field for field in REQUIRED_TEAM_METRIC_FIELDS
        if _number_or_none(team_metrics.get(field)) is None
    ]

    if not present_fields:
        return {
            "status": "missing",
            "source_label": "missing",
            "field_count": 0,
            "required_field_count": len(REQUIRED_TEAM_METRIC_FIELDS),
            "missing_fields": missing_fields,
            "message": "Team metrics are unavailable for this fixture.",
        }

    if missing_fields:
        return {
            "status": "partial",
            "source_label": "static_curated",
            "field_count": len(present_fields),
            "required_field_count": len(REQUIRED_TEAM_METRIC_FIELDS),
            "missing_fields": missing_fields,
            "message": "Team metrics are partially available from static curated references.",
        }

    return {
        "status": "complete",
        "source_label": "static_curated",
        "field_count": len(present_fields),
        "required_field_count": len(REQUIRED_TEAM_METRIC_FIELDS),
        "missing_fields": [],
        "message": "Team metrics are static curated reference values, not live matchday research.",
    }


def build_radar_quality(metrics: dict, team1: str, team2: str) -> dict:
    missing_by_team = {}
    for team in (team1, team2):
        team_metrics = metrics.get(team) or {}
        missing = [
            field for field in RADAR_METRIC_FIELDS
            if _number_or_none(team_metrics.get(field)) is None
        ]
        if missing:
            missing_by_team[team] = missing

    if missing_by_team:
        return {
            "status": "unavailable",
            "source_label": "missing",
            "missing_fields": missing_by_team,
            "message": "Radar chart is unavailable because required team metrics are missing.",
        }

    return {
        "status": "available",
        "source_label": "static_curated",
        "missing_fields": {},
        "message": "Radar chart uses static curated team metrics.",
    }


def build_metrics_data_quality(
    metrics_data: dict,
    team1: str,
    team2: str,
    elo_t1: Optional[float],
    elo_t2: Optional[float],
) -> dict:
    forecast = metrics_data.get("dixon_coles_forecast") or {}
    default_forecast = is_default_forecast(forecast)
    forecast_quality = {
        "status": "unavailable" if default_forecast else "available",
        "source_label": "default_forecast" if default_forecast else "hardcoded_reference",
        "message": (
            "Stored forecast is the default 40/30/30 fallback and should not be displayed as a model probability."
            if default_forecast
            else "Stored forecast is an Elo-derived Dixon-Coles calculation using local reference ratings."
        ),
    }

    team_metrics = metrics_data.get("team_metrics") or {}
    team_quality = {
        team1: build_team_metric_quality(team_metrics, team1),
        team2: build_team_metric_quality(team_metrics, team2),
    }

    viz_team1 = get_visualization_proxy(team1)
    viz_team2 = get_visualization_proxy(team2)

    return {
        "forecast": forecast_quality,
        "score_probabilities": {
            "status": "unavailable" if default_forecast else "available",
            "source_label": "default_forecast" if default_forecast else "hardcoded_reference",
            "message": (
                "Exact-score probabilities are hidden because the fixture only has the default forecast fallback."
                if default_forecast
                else "Exact-score probabilities come from the stored Dixon-Coles score grid."
            ),
        },
        "team_metrics": team_quality,
        "radar_metrics": build_radar_quality(team_metrics, team1, team2),
        "elo_ratings": {
            team1: {
                "status": "available" if elo_t1 is not None else "missing",
                "source_label": "hardcoded_reference" if elo_t1 is not None else "missing",
                "message": "Local fallback Elo-style reference, not a live rating feed.",
            },
            team2: {
                "status": "available" if elo_t2 is not None else "missing",
                "source_label": "hardcoded_reference" if elo_t2 is not None else "missing",
                "message": "Local fallback Elo-style reference, not a live rating feed.",
            },
        },
        "monte_carlo_projections": {
            "status": "deterministic_fallback" if elo_t1 is not None and elo_t2 is not None else "unavailable",
            "source_label": "hardcoded_reference",
            "message": "Current progression values are deterministic Elo curves, not random-trial Monte Carlo simulation.",
        },
        "visualizations": {
            "status": "proxy_historical",
            "source_label": "proxy_historical",
            "teams": {
                team1: (viz_team1 or {}).get("label", "Historical proxy match"),
                team2: (viz_team2 or {}).get("label", "Historical proxy match"),
            },
            "message": "Event visualizations use historical StatsBomb proxy matches, not World Cup 2026 event data.",
        },
    }


def compute_monte_carlo_probs(elo: Optional[float]) -> dict:
    if elo is None:
        return {"r16": "N/A", "qf": "N/A", "sf": "N/A", "final": "N/A", "win": "N/A"}
    base = 1400.0
    diff = max(0.0, elo - base)
    scale = 730.0
    r16 = 0.40 + 0.59 * (diff / scale)
    qf = 0.15 + 0.75 * (diff / scale) ** 2
    sf = 0.05 + 0.75 * (diff / scale) ** 3
    final = 0.02 + 0.58 * (diff / scale) ** 4
    win = 0.005 + 0.395 * (diff / scale) ** 5
    return {
        "r16": min(0.999, max(0.05, r16)),
        "qf": min(0.95, max(0.02, qf)),
        "sf": min(0.85, max(0.01, sf)),
        "final": min(0.65, max(0.005, final)),
        "win": min(0.45, max(0.001, win))
    }

# --- REST ENDPOINTS ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/schedule")
def get_schedule():
    matches_dir = DATA_DIR / "matches"
    matches_details = []
    now_value = datetime.now().replace(microsecond=0)
    next_24h_end = now_value + timedelta(hours=24)
    live_game_index, schedule_source = fetch_live_games_for_schedule()

    if matches_dir.exists():
        for folder in sorted(matches_dir.iterdir()):
            if folder.is_dir() and folder.name.endswith("_2026"):
                sum_path = folder / "summary.json"
                if sum_path.exists():
                    try:
                        with open(sum_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        meta = data.get("metadata", {})
                        lifecycle = schedule_lifecycle(
                            meta,
                            live_game_index.get(folder.name),
                            now_value,
                            next_24h_end,
                        )
                        matches_details.append({
                            "id": folder.name,
                            "team1": meta.get("team1"),
                            "team2": meta.get("team2"),
                            "date": meta.get("date"),
                            "time": meta.get("time"),
                            "venue": meta.get("venue"),
                            "stage": meta.get("stage"),
                            **lifecycle,
                        })
                    except Exception:
                        pass

    matches_details.sort(
        key=lambda item: (
            parse_schedule_datetime(item.get("date"), item.get("time")) or datetime.max,
            item.get("id") or "",
        )
    )

    day_matches = [item for item in matches_details if item.get("lifecycle") == "today"]
    first_kickoff = None
    if day_matches:
        day_kickoffs = [
            kickoff for kickoff in (
                parse_schedule_datetime(item.get("date"), item.get("time"))
                for item in day_matches
            )
            if kickoff
        ]
        first_kickoff = min(day_kickoffs) if day_kickoffs else None
    briefing_window_start = first_kickoff - timedelta(hours=3) if first_kickoff else None

    lifecycle_counts: dict[str, int] = {}
    for item in matches_details:
        state = item.get("lifecycle") or "unknown"
        lifecycle_counts[state] = lifecycle_counts.get(state, 0) + 1

    return {
        "matches": matches_details,
        "schedule_source": schedule_source,
        "active_date": now_value.strftime("%m/%d/%Y"),
        "default_match_id": day_matches[0]["id"] if day_matches else None,
        "lifecycle_counts": lifecycle_counts,
        "briefing_window": {
            "first_kickoff": first_kickoff.isoformat(timespec="minutes") if first_kickoff else None,
            "window_start": briefing_window_start.isoformat(timespec="minutes") if briefing_window_start else None,
            "window_hours": 3,
            "is_open": bool(
                first_kickoff
                and briefing_window_start
                and briefing_window_start <= now_value <= first_kickoff
            ),
        },
    }

@app.get("/api/match/{match_id}/summary")
def get_match_summary(match_id: str):
    sum_path = DATA_DIR / "matches" / match_id / "summary.json"
    if not sum_path.exists():
        raise HTTPException(status_code=404, detail="Summary payload not found")
    with open(sum_path, "r", encoding="utf-8") as f:
        summary_data = json.load(f)

    briefing_path = DATA_DIR / "matches" / match_id / "briefing.json"
    if briefing_path.exists():
        try:
            with open(briefing_path, "r", encoding="utf-8") as f:
                briefing_data = json.load(f)
            freshness = (
                briefing_data.get("data_quality", {}).get("freshness_state")
                or briefing_data.get("metadata", {}).get("freshness_state")
                or "stale"
            )
            summary_data["briefing_status"] = {
                "freshness_state": freshness,
                "source_label": briefing_data.get("source_label", "web_researched"),
                "message": "Last-minute briefing artifact is available.",
            }
        except Exception:
            summary_data["briefing_status"] = {
                "freshness_state": "blocked",
                "source_label": "blocked",
                "message": "Briefing artifact exists but could not be read.",
            }
    else:
        summary_data["briefing_status"] = {
            "freshness_state": "baseline_only",
            "source_label": "static_curated",
            "message": "Static baseline preview only; no last-minute briefing has been generated.",
        }

    return summary_data

@app.get("/api/match/{match_id}/metrics")
def get_match_metrics(match_id: str):
    met_path = DATA_DIR / "matches" / match_id / "metrics.json"
    if not met_path.exists():
        raise HTTPException(status_code=404, detail="Metrics payload not found")
    with open(met_path, "r", encoding="utf-8") as f:
        metrics_data = json.load(f)

    team1, team2 = load_match_team_names(match_id)
    if not team1 or not team2:
        raise HTTPException(status_code=422, detail="Match teams could not be resolved")

    sd_client = SoccerDataClient()
    elo_data_t1 = sd_client.fetch_club_elo_ratings(team1)
    elo_data_t2 = sd_client.fetch_club_elo_ratings(team2)
    elo_t1 = elo_data_t1.get("elo_rating") if elo_data_t1 else None
    elo_t2 = elo_data_t2.get("elo_rating") if elo_data_t2 else None

    metrics_data["elo_ratings"] = {
        team1: elo_t1,
        team2: elo_t2
    }
    metrics_data["monte_carlo_projections"] = {
        team1: compute_monte_carlo_probs(elo_t1),
        team2: compute_monte_carlo_probs(elo_t2)
    }
    # Source of the StatsBomb event visualizations (proxy historical matches —
    # no real 2026 event data exists yet), surfaced so the UI can label them honestly.
    metrics_data["viz_proxies"] = {
        team1: (get_visualization_proxy(team1) or {}).get("label", "Historical proxy match"),
        team2: (get_visualization_proxy(team2) or {}).get("label", "Historical proxy match"),
    }
    metrics_data["data_quality"] = build_metrics_data_quality(metrics_data, team1, team2, elo_t1, elo_t2)

    return metrics_data

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
    t1_name, t2_name = load_match_team_names(match_id)
    if not t1_name or not t2_name:
        raise HTTPException(status_code=422, detail="Match teams could not be resolved")

    active_team = t1_name if team is None or clean_team_name(team) == clean_team_name(t1_name) else t2_name
    proxy = get_visualization_proxy(active_team) or MATCH_VISUALIZATION_PROXIES["Netherlands"]

    client = bigquery.Client()
    img_bytes = None

    try:
        if viz_type == "momentum":
            proxy1 = get_visualization_proxy(t1_name) or MATCH_VISUALIZATION_PROXIES["Netherlands"]
            proxy2 = get_visualization_proxy(t2_name) or MATCH_VISUALIZATION_PROXIES["Japan"]
            img_bytes = get_cached_xg_distribution(client, proxy1["match_id"], proxy1["team"], t1_name, proxy2["match_id"], proxy2["team"], t2_name)
        elif viz_type == "passing_network":
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
            proxy1 = get_visualization_proxy(t1_name)
            proxy2 = get_visualization_proxy(t2_name)
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
