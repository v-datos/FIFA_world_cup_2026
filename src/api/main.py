import os
import sys
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
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
from src.analytics.squad_style_sources import apply_squad_style_source_cache
from src.analytics.monte_carlo_simulation import (
    DEFAULT_SIMULATION_COUNT,
    DEFAULT_SIMULATION_SEED,
    run_tournament_monte_carlo,
)
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
_monte_carlo_cache = {}

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


def get_monte_carlo_simulation(simulation_count: int, seed: int) -> dict:
    cache_key = (simulation_count, seed)
    if cache_key not in _monte_carlo_cache:
        _monte_carlo_cache[cache_key] = run_tournament_monte_carlo(
            simulation_count=simulation_count,
            seed=seed,
        )
    return _monte_carlo_cache[cache_key]


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


def build_team_metric_quality(
    metrics: dict,
    team: str,
    field_sources: Optional[dict[str, dict]] = None,
    source_metadata: Optional[dict] = None,
) -> dict:
    team_metrics = metrics.get(team) or {}
    field_sources = field_sources or {}
    source_metadata = source_metadata or {}
    present_fields = [
        field for field in REQUIRED_TEAM_METRIC_FIELDS
        if _number_or_none(team_metrics.get(field)) is not None
    ]
    missing_fields = [
        field for field in REQUIRED_TEAM_METRIC_FIELDS
        if _number_or_none(team_metrics.get(field)) is None
    ]
    fields = {}
    source_backed_fields = []
    static_fields = []
    approximation_fields = []

    for field in REQUIRED_TEAM_METRIC_FIELDS:
        value = _number_or_none(team_metrics.get(field))
        source_record = field_sources.get(field)
        if value is not None and source_record:
            source_status = source_record.get("source_status") or "source_backed"
            source_label = source_record.get("source_label", "web_researched")
            fields[field] = {
                "status": "available",
                "source_status": source_status,
                "source_label": source_label,
                "source_name": source_record.get("source_name"),
                "source_url": source_record.get("source_url"),
                "checked_at_utc": source_record.get("checked_at_utc"),
                "unit": source_record.get("unit"),
                "value": value,
                "source_value_text": source_record.get("source_value_text"),
                "approximation": source_record.get("approximation", False),
                "approximation_note": source_record.get("approximation_note"),
                "previous_static_value": source_record.get("previous_static_value"),
                "overrode_static_value": source_record.get("overrode_static_value", False),
                "message": "Field value comes from the T-038 source cache.",
            }
            source_backed_fields.append(field)
            if source_record.get("approximation"):
                approximation_fields.append(field)
        elif value is not None:
            fields[field] = {
                "status": "available",
                "source_status": "hardcoded_reference_unverified",
                "source_label": "hardcoded_reference",
                "value": value,
                "message": "Stored local profile metric; no T-038 field-level source cache record is available.",
            }
            static_fields.append(field)
        else:
            fields[field] = {
                "status": "missing",
                "source_status": "missing",
                "source_label": "missing",
                "source_name": source_metadata.get("source_name"),
                "checked_at_utc": source_metadata.get("checked_at_utc"),
                "source_cache_status": source_metadata.get("status"),
                "missing_reasons": source_metadata.get("missing_reasons", []),
                "blocked_reasons": source_metadata.get("blocked_reasons", []),
                "value": None,
                "message": "No stored or source-backed field value is available from the current squad/style source cache.",
            }

    if not present_fields:
        return {
            "status": "missing",
            "source_status": "missing",
            "source_label": "missing",
            "source_labels": ["missing"],
            "checked_at_utc": source_metadata.get("checked_at_utc"),
            "field_count": 0,
            "source_backed_field_count": 0,
            "static_field_count": 0,
            "required_field_count": len(REQUIRED_TEAM_METRIC_FIELDS),
            "source_cache_status": source_metadata.get("status"),
            "missing_reasons": source_metadata.get("missing_reasons", []),
            "blocked_reasons": source_metadata.get("blocked_reasons", []),
            "missing_fields": missing_fields,
            "source_backed_fields": [],
            "static_fields": [],
            "approximation_fields": [],
            "fields": fields,
            "field_sources": fields,
            "message": "Team metrics are unavailable for this fixture.",
        }

    source_labels = sorted(
        {
            fields[field]["source_label"]
            for field in present_fields
            if fields.get(field, {}).get("source_label")
        }
    )
    source_status = "hardcoded_reference"
    if source_backed_fields and (static_fields or missing_fields):
        source_status = "partial_source_backed"
    elif source_backed_fields:
        source_status = "source_backed"

    if missing_fields:
        return {
            "status": "partial",
            "source_status": source_status,
            "source_label": "web_researched" if source_backed_fields else "hardcoded_reference",
            "source_labels": source_labels,
            "field_count": len(present_fields),
            "source_backed_field_count": len(source_backed_fields),
            "static_field_count": len(static_fields),
            "required_field_count": len(REQUIRED_TEAM_METRIC_FIELDS),
            "missing_fields": missing_fields,
            "source_backed_fields": source_backed_fields,
            "static_fields": static_fields,
            "approximation_fields": approximation_fields,
            "fields": fields,
            "field_sources": fields,
            "message": (
                f"{len(source_backed_fields)} team metric fields are source-backed; "
                f"{len(missing_fields)} required fields remain missing."
                if source_backed_fields
                else "Team metrics are partially available from local profile references."
            ),
        }

    return {
        "status": "complete",
        "source_status": source_status,
        "source_label": "web_researched" if source_backed_fields else "hardcoded_reference",
        "source_labels": source_labels,
        "field_count": len(present_fields),
        "source_backed_field_count": len(source_backed_fields),
        "static_field_count": len(static_fields),
        "required_field_count": len(REQUIRED_TEAM_METRIC_FIELDS),
        "missing_fields": [],
        "source_backed_fields": source_backed_fields,
        "static_fields": static_fields,
        "approximation_fields": approximation_fields,
        "fields": fields,
        "field_sources": fields,
        "message": (
            f"{len(source_backed_fields)} team metric fields are source-backed; "
            "remaining available fields are stored local profile references."
            if source_backed_fields
            else "Team metrics are local profile reference values, not live matchday research."
        ),
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
        "source_label": "hardcoded_reference",
        "missing_fields": {},
        "message": "Radar chart uses local profile reference metrics.",
    }


def build_metrics_data_quality(
    metrics_data: dict,
    team1: str,
    team2: str,
    elo_t1: Optional[float],
    elo_t2: Optional[float],
    elo_data_t1: Optional[dict] = None,
    elo_data_t2: Optional[dict] = None,
    simulation_metadata: Optional[dict] = None,
    team_metric_source_data: Optional[dict] = None,
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
    team_metric_sources = (team_metric_source_data or {}).get("teams", {})
    team_metric_team_metadata = (team_metric_source_data or {}).get("team_metadata", {})
    team_metric_source_metadata = (team_metric_source_data or {}).get("metadata", {})
    teams_with_manifest_rows = set(
        team_metric_source_metadata.get("teams_with_manifest_rows", [])
    )

    def source_metadata_for_team(team: str) -> dict:
        if team_metric_team_metadata.get(team):
            return team_metric_team_metadata[team]
        if team in teams_with_manifest_rows or team in team_metric_sources:
            return team_metric_source_metadata
        return {}

    team1_source_metadata = source_metadata_for_team(team1)
    team2_source_metadata = source_metadata_for_team(team2)
    team_quality = {
        team1: build_team_metric_quality(
            team_metrics,
            team1,
            team_metric_sources.get(team1),
            team1_source_metadata,
        ),
        team2: build_team_metric_quality(
            team_metrics,
            team2,
            team_metric_sources.get(team2),
            team2_source_metadata,
        ),
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
        "team_metric_source_cache": (team_metric_source_data or {}).get(
            "metadata",
            {
                "status": "missing_cache",
                "source_label": "missing",
                "message": "Squad/style source cache metadata is unavailable.",
            },
        ),
        "radar_metrics": build_radar_quality(team_metrics, team1, team2),
        "elo_ratings": {
            team1: {
                "status": "available" if elo_t1 is not None else "missing",
                "source_label": (elo_data_t1 or {}).get("source_label", "missing"),
                "source_name": (elo_data_t1 or {}).get("source_name"),
                "source_url": (elo_data_t1 or {}).get("source_url"),
                "checked_at_utc": (elo_data_t1 or {}).get("checked_at_utc"),
                "message": (
                    "Source-backed World Football Elo national-team rating."
                    if (elo_data_t1 or {}).get("source_label") == "web_researched"
                    else "Local fallback Elo-style reference, not a live rating feed."
                ),
            },
            team2: {
                "status": "available" if elo_t2 is not None else "missing",
                "source_label": (elo_data_t2 or {}).get("source_label", "missing"),
                "source_name": (elo_data_t2 or {}).get("source_name"),
                "source_url": (elo_data_t2 or {}).get("source_url"),
                "checked_at_utc": (elo_data_t2 or {}).get("checked_at_utc"),
                "message": (
                    "Source-backed World Football Elo national-team rating."
                    if (elo_data_t2 or {}).get("source_label") == "web_researched"
                    else "Local fallback Elo-style reference, not a live rating feed."
                ),
            },
        },
        "monte_carlo_projections": build_monte_carlo_quality(simulation_metadata),
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


def build_monte_carlo_quality(simulation_metadata: Optional[dict]) -> dict:
    if not simulation_metadata or simulation_metadata.get("method") != "random_trial_monte_carlo":
        return {
            "status": "unavailable",
            "source_label": "missing",
            "message": "Tournament simulation is unavailable because bracket data could not be loaded.",
        }

    simulation_count = simulation_metadata.get("simulation_count")
    seed = simulation_metadata.get("seed")
    rating_source = simulation_metadata.get("rating_source", "hardcoded_reference")
    source_label = simulation_metadata.get("source_label", rating_source)
    return {
        "status": "simulation",
        "source_label": source_label,
        "projection_method": simulation_metadata.get("method"),
        "simulation_count": simulation_count,
        "seed": seed,
        "generated_at_utc": simulation_metadata.get("generated_at_utc"),
        "model_version": simulation_metadata.get("model_version"),
        "rating_source": rating_source,
        "rating_status": simulation_metadata.get("rating_status"),
        "missing_rating_teams": simulation_metadata.get("missing_rating_teams", []),
        "message": (
            f"Random-trial Monte Carlo simulation with {simulation_count:,} trials and seed {seed}. "
            f"Ratings use {rating_source}."
        ),
    }


BRIEFING_FRESHNESS_STATES = {"fresh", "stale", "baseline_only", "blocked", "skipped"}
BRIEFING_REQUIRED_BLOCKS = {
    "metadata",
    "fixture",
    "team_keys",
    "briefing",
    "forecast_snapshot",
    "data_quality",
    "sources",
    "review",
}


def load_match_summary_payload(match_id: str) -> dict:
    summary_path = DATA_DIR / "matches" / match_id / "summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Summary payload not found")
    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)


def relative_project_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def parse_utc_timestamp(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def briefing_source_label(sources: Any, freshness_state: str) -> tuple[str, list[str]]:
    if freshness_state in {"blocked", "skipped"}:
        return "blocked", ["blocked"]

    source_labels = []
    if isinstance(sources, list):
        for source in sources:
            if not isinstance(source, dict):
                continue
            label = source.get("label") or source.get("source_label")
            if label and label not in source_labels:
                source_labels.append(label)

    if "web_researched" in source_labels:
        return "web_researched", source_labels
    if "live_schedule" in source_labels:
        return "live_schedule", source_labels
    if source_labels:
        return source_labels[0], source_labels
    return "static_curated", ["static_curated"]


def briefing_status_message(freshness_state: str, source_label: str, expired: bool = False) -> str:
    if freshness_state == "fresh" and source_label == "web_researched":
        return "Fresh source-backed match briefing is available."
    if freshness_state == "fresh":
        return "Fresh briefing artifact is available, but it is not source-backed match research."
    if freshness_state == "stale" and expired:
        return "Briefing artifact exists but its validity window has expired."
    if freshness_state == "stale":
        return "Briefing artifact exists but is outside the configured last-minute window."
    if freshness_state == "blocked":
        return "Briefing generation was blocked; use the static baseline preview until inputs are resolved."
    if freshness_state == "skipped":
        return "Briefing generation was skipped for this fixture."
    if freshness_state == "invalid":
        return "Briefing artifact exists but is invalid; use the static baseline preview."
    return "Static baseline preview only; no last-minute briefing has been generated."


def baseline_briefing_payload(
    match_id: str,
    summary_data: dict,
    freshness_state: str = "baseline_only",
    warning: Optional[str] = None,
) -> dict:
    summary_path = DATA_DIR / "matches" / match_id / "summary.json"
    briefing_path = DATA_DIR / "matches" / match_id / "briefing.json"
    status = {
        "freshness_state": freshness_state,
        "source_label": "blocked" if freshness_state == "invalid" else "static_curated",
        "source_labels": ["blocked"] if freshness_state == "invalid" else ["static_curated"],
        "generated_at_utc": None,
        "valid_until_utc": None,
        "checked_at_utc": None,
        "review_status": "not_generated" if freshness_state == "baseline_only" else "invalid",
        "has_artifact": freshness_state == "invalid",
        "artifact_status": "invalid" if freshness_state == "invalid" else "missing",
        "artifact_path": relative_project_path(briefing_path),
        "message": briefing_status_message(freshness_state, "static_curated"),
    }
    warnings = [warning] if warning else []
    return {
        "metadata": {
            "schema_version": "1.0",
            "match_id": match_id,
            "generated_at_utc": None,
            "generator": None,
            "mode": "baseline_preview",
            "freshness": freshness_state,
            "valid_until_utc": None,
            "briefing_window_hours": 3,
        },
        "fixture": summary_data.get("metadata", {}),
        "team_keys": {
            "team1": canonical_team_slug(summary_data.get("metadata", {}).get("team1", "")),
            "team2": canonical_team_slug(summary_data.get("metadata", {}).get("team2", "")),
        },
        "briefing": None,
        "forecast_snapshot": {},
        "data_quality": {
            "freshness_state": freshness_state,
            "warnings": warnings,
            "blocked_reasons": warnings if freshness_state == "invalid" else [],
        },
        "sources": [
            {
                "name": "summary.json",
                "path_or_url": relative_project_path(summary_path),
                "label": "static_curated",
                "status": "used",
                "checked_at_utc": None,
                "collection_method": "local_file",
            }
        ],
        "review": {
            "status": "not_generated" if freshness_state == "baseline_only" else "invalid",
            "reviewer": None,
            "reviewed_at_utc": None,
            "notes": warning,
        },
        "briefing_status": status,
    }


def briefing_status_from_artifact(match_id: str, briefing_data: Any) -> tuple[Optional[dict], Optional[str]]:
    if not isinstance(briefing_data, dict):
        return None, "briefing.json root must be an object."

    missing_blocks = sorted(BRIEFING_REQUIRED_BLOCKS - set(briefing_data))
    if missing_blocks:
        return None, f"briefing.json is missing required blocks: {', '.join(missing_blocks)}."

    metadata = briefing_data.get("metadata") or {}
    data_quality = briefing_data.get("data_quality") or {}
    if not isinstance(metadata, dict) or not isinstance(data_quality, dict):
        return None, "briefing.json metadata and data_quality must be objects."

    artifact_match_id = metadata.get("match_id")
    if artifact_match_id and artifact_match_id != match_id:
        return None, f"briefing.json match_id {artifact_match_id!r} does not match route {match_id!r}."

    freshness_state = (
        data_quality.get("freshness_state")
        or metadata.get("freshness")
        or metadata.get("freshness_state")
    )
    if not isinstance(freshness_state, str) or not freshness_state:
        return None, "briefing.json does not declare a freshness state."
    freshness_state = freshness_state.strip().lower()
    if freshness_state not in BRIEFING_FRESHNESS_STATES:
        return None, f"briefing.json freshness state {freshness_state!r} is unsupported."

    expired = False
    valid_until = metadata.get("valid_until_utc")
    valid_until_dt = parse_utc_timestamp(valid_until)
    if freshness_state == "fresh" and valid_until_dt and valid_until_dt < datetime.now(timezone.utc):
        freshness_state = "stale"
        expired = True

    source_label, source_labels = briefing_source_label(briefing_data.get("sources", []), freshness_state)
    review = briefing_data.get("review") if isinstance(briefing_data.get("review"), dict) else {}
    generated_at = metadata.get("generated_at_utc")
    checked_at = generated_at
    if isinstance(briefing_data.get("sources"), list):
        for source in briefing_data["sources"]:
            if isinstance(source, dict) and source.get("checked_at_utc"):
                checked_at = source.get("checked_at_utc")
                break

    return {
        "freshness_state": freshness_state,
        "source_label": source_label,
        "source_labels": source_labels,
        "generated_at_utc": generated_at,
        "valid_until_utc": valid_until,
        "checked_at_utc": checked_at,
        "review_status": review.get("status"),
        "has_artifact": True,
        "artifact_status": "available",
        "artifact_path": relative_project_path(DATA_DIR / "matches" / match_id / "briefing.json"),
        "message": briefing_status_message(freshness_state, source_label, expired),
    }, None


def build_match_briefing_payload(match_id: str, summary_data: Optional[dict] = None) -> dict:
    summary_data = summary_data or load_match_summary_payload(match_id)
    briefing_path = DATA_DIR / "matches" / match_id / "briefing.json"

    if not briefing_path.exists():
        return baseline_briefing_payload(match_id, summary_data)

    try:
        with open(briefing_path, "r", encoding="utf-8") as f:
            briefing_data = json.load(f)
    except Exception as exc:
        return baseline_briefing_payload(match_id, summary_data, "invalid", str(exc))

    status, error = briefing_status_from_artifact(match_id, briefing_data)
    if error:
        return baseline_briefing_payload(match_id, summary_data, "invalid", error)

    response = dict(briefing_data)
    response["briefing_status"] = status
    return response

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
    summary_data = load_match_summary_payload(match_id)
    summary_data["briefing_status"] = build_match_briefing_payload(
        match_id,
        summary_data,
    )["briefing_status"]

    return summary_data


@app.get("/api/match/{match_id}/briefing")
def get_match_briefing(match_id: str):
    return build_match_briefing_payload(match_id)


@app.get("/api/match/{match_id}/metrics")
def get_match_metrics(
    match_id: str,
    simulation_count: int = DEFAULT_SIMULATION_COUNT,
    seed: int = DEFAULT_SIMULATION_SEED,
):
    if simulation_count < DEFAULT_SIMULATION_COUNT or simulation_count > 50_000:
        raise HTTPException(
            status_code=422,
            detail="simulation_count must be between 10000 and 50000",
        )

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

    simulation = get_monte_carlo_simulation(simulation_count, seed)
    simulation_metadata = simulation.get("metadata")
    metrics_data["monte_carlo_projections"] = simulation.get("probabilities", {})
    metrics_data["monte_carlo_metadata"] = simulation_metadata
    # Source of the StatsBomb event visualizations (proxy historical matches —
    # no real 2026 event data exists yet), surfaced so the UI can label them honestly.
    metrics_data["viz_proxies"] = {
        team1: (get_visualization_proxy(team1) or {}).get("label", "Historical proxy match"),
        team2: (get_visualization_proxy(team2) or {}).get("label", "Historical proxy match"),
    }
    team_metric_source_data = apply_squad_style_source_cache(
        metrics_data,
        match_id,
        (team1, team2),
        REQUIRED_TEAM_METRIC_FIELDS,
    )
    metrics_data["team_metric_source_cache"] = team_metric_source_data.get("metadata", {})
    metrics_data["team_metric_sources"] = team_metric_source_data.get("teams", {})
    metrics_data["data_quality"] = build_metrics_data_quality(
        metrics_data,
        team1,
        team2,
        elo_t1,
        elo_t2,
        elo_data_t1,
        elo_data_t2,
        simulation_metadata,
        team_metric_source_data,
    )

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
