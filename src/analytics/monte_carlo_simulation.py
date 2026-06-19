"""Seeded random-trial tournament simulation for World Cup progression."""

from __future__ import annotations

import json
import math
import random
import subprocess
from itertools import combinations
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analytics.soccerdata_client import SoccerDataClient
from src.common.team_identity import normalize_team_name, team_id_to_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
GRID_STATE_PATH = DATA_DIR / "bracket" / "grid_state.json"
DEFAULT_GAMES_CACHE = Path("/tmp/games.json")
LIVE_GAMES_URL = "https://worldcup26.ir/get/games"
MODEL_VERSION = "mc-2026.1"
DEFAULT_SIMULATION_COUNT = 10_000
DEFAULT_SIMULATION_SEED = 20260618
NEUTRAL_ELO = 1500.0
STAGE_KEYS = ("group_advancement", "r32", "r16", "qf", "sf", "final", "win")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_games(payload: Any) -> list[dict[str, Any]]:
    games = payload.get("games", []) if isinstance(payload, dict) else payload
    return [game for game in games if isinstance(game, dict)] if isinstance(games, list) else []


def fetch_games(cache_path: Path = DEFAULT_GAMES_CACHE) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors: list[str] = []
    try:
        result = subprocess.run(
            ["curl", "-s", "-k", "--max-time", "10", LIVE_GAMES_URL],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            games = extract_games(json.loads(result.stdout))
            if games:
                return games, {
                    "source_label": "live_schedule",
                    "source_name": "worldcup26.ir games API",
                    "source_url": LIVE_GAMES_URL,
                    "collection_method": "api",
                    "status": "used",
                    "checked_at_utc": utc_now(),
                }
            errors.append("live API returned no games")
        else:
            errors.append(f"live API curl exit {result.returncode}")
    except Exception as exc:
        errors.append(f"live API failed: {exc}")

    try:
        games = extract_games(load_json(cache_path))
        if games:
            return games, {
                "source_label": "live_schedule",
                "source_name": "cached games payload",
                "source_url": str(cache_path),
                "collection_method": "cache",
                "status": "used",
                "checked_at_utc": utc_now(),
                "warnings": errors,
            }
    except Exception as exc:
        errors.append(f"cache failed: {exc}")

    return [], {
        "source_label": "blocked",
        "source_name": "games schedule",
        "source_url": LIVE_GAMES_URL,
        "collection_method": "api",
        "status": "blocked",
        "checked_at_utc": utc_now(),
        "warnings": errors,
        "blocked_reasons": errors or ["games_source_unavailable"],
    }


def game_team_names(game: dict[str, Any]) -> tuple[str, str]:
    home = (
        game.get("home_team_name_en")
        or game.get("home_team_label")
        or team_id_to_name(game.get("home_team_id"))
        or ""
    )
    away = (
        game.get("away_team_name_en")
        or game.get("away_team_label")
        or team_id_to_name(game.get("away_team_id"))
        or ""
    )
    return normalize_team_name(home), normalize_team_name(away)


def game_finished(game: dict[str, Any]) -> bool:
    value = game.get("finished")
    return value is True or str(value).upper() == "TRUE"


def int_score(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def group_letter(group_name: str) -> str:
    return str(group_name).replace("Group", "").strip().upper()


def base_row(team: str, group: str) -> dict[str, Any]:
    return {
        "team": team,
        "group": group,
        "p": 0,
        "w": 0,
        "d": 0,
        "l": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "pts": 0,
    }


def base_groups(grid_state: dict[str, Any], games: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for group in grid_state.get("groups", []):
        letter = group_letter(group.get("name", ""))
        groups[letter] = {}
        for row in group.get("standings", []):
            team = normalize_team_name(row.get("team") or "")
            if not team:
                continue
            gf = int_score(row.get("gf"))
            ga = int_score(row.get("ga"))
            groups[letter][team] = {
                "team": team,
                "group": letter,
                "p": int_score(row.get("p")),
                "w": int_score(row.get("w")),
                "d": int_score(row.get("d")),
                "l": int_score(row.get("l")),
                "gf": gf,
                "ga": ga,
                "gd": gf - ga,
                "pts": int_score(row.get("pts")),
            }

    finished_group_games: list[dict[str, Any]] = [
        game
        for game in games
        if str(game.get("type") or "").lower() == "group" and game_finished(game)
    ]

    for game in games:
        if str(game.get("type") or "").lower() != "group":
            continue
        letter = str(game.get("group") or "").strip().upper()
        if not letter:
            continue
        groups.setdefault(letter, {})
        for team in game_team_names(game):
            if team and team not in groups[letter]:
                groups[letter][team] = base_row(team, letter)

    if finished_group_games:
        live_groups = {
            group: {team: base_row(team, group) for team in rows}
            for group, rows in groups.items()
        }
        for game in finished_group_games:
            letter = str(game.get("group") or "").strip().upper()
            team1, team2 = game_team_names(game)
            if not letter or not team1 or not team2:
                continue
            live_groups.setdefault(letter, {})
            live_groups[letter].setdefault(team1, base_row(team1, letter))
            live_groups[letter].setdefault(team2, base_row(team2, letter))
            score1 = int_score(game.get("home_score"))
            score2 = int_score(game.get("away_score"))
            update_standing(live_groups[letter][team1], score1, score2)
            update_standing(live_groups[letter][team2], score2, score1)
        for group, rows in live_groups.items():
            if any(row.get("p", 0) for row in rows.values()):
                groups[group] = rows
    return groups


def build_ratings(teams: list[str]) -> tuple[dict[str, float], dict[str, Any]]:
    client = SoccerDataClient()
    ratings: dict[str, float] = {}
    missing: list[str] = []
    sources: set[str] = set()
    source_urls: set[str] = set()
    checked_times: set[str] = set()
    for team in sorted(set(teams)):
        rating = None
        data = client.fetch_club_elo_ratings(team)
        if data:
            rating = data.get("elo_rating")
            source_label = data.get("source_label")
            if source_label:
                sources.add(source_label)
            if data.get("source_url"):
                source_urls.add(str(data["source_url"]))
            if data.get("checked_at_utc"):
                checked_times.add(str(data["checked_at_utc"]))
        if rating is None:
            ratings[team] = NEUTRAL_ELO
            missing.append(team)
        else:
            ratings[team] = float(rating)

    if sources == {"web_researched"} and not missing:
        rating_source = "world_football_elo"
        rating_status = "complete"
        source_label = "web_researched"
        message = "Simulation uses cached World Football Elo national-team ratings."
    elif "web_researched" in sources:
        rating_source = "world_football_elo_with_fallbacks"
        rating_status = "partial_neutral_defaults" if missing else "partial"
        source_label = "web_researched"
        message = (
            "Simulation uses cached World Football Elo ratings where available; "
            "missing teams use neutral defaults."
        )
    else:
        rating_source = "hardcoded_reference"
        rating_status = "partial_neutral_defaults" if missing else "complete"
        source_label = "hardcoded_reference"
        message = (
            "Simulation uses local Elo-style reference ratings; missing teams use neutral defaults. "
            "Refresh the World Football Elo cache with T-039 tooling to replace this fallback."
        )

    return ratings, {
        "rating_source": rating_source,
        "rating_status": rating_status,
        "source_label": source_label,
        "source_urls": sorted(source_urls),
        "source_checked_at_utc": sorted(checked_times)[-1] if checked_times else None,
        "neutral_default_elo": NEUTRAL_ELO,
        "missing_rating_teams": missing,
        "message": message,
    }


def expected_goals(team_rating: float, opponent_rating: float) -> tuple[float, float]:
    diff = (team_rating - opponent_rating) / 400.0
    team_lambda = 1.25 * math.exp(0.42 * diff)
    opp_lambda = 1.15 * math.exp(-0.42 * diff)
    return max(0.2, min(3.4, team_lambda)), max(0.2, min(3.4, opp_lambda))


def sample_poisson(rng: random.Random, lam: float) -> int:
    threshold = math.exp(-lam)
    product = 1.0
    count = 0
    while product > threshold:
        count += 1
        product *= rng.random()
    return count - 1


def simulate_score(team1: str, team2: str, ratings: dict[str, float], rng: random.Random) -> tuple[int, int]:
    lam1, lam2 = expected_goals(ratings.get(team1, NEUTRAL_ELO), ratings.get(team2, NEUTRAL_ELO))
    return sample_poisson(rng, lam1), sample_poisson(rng, lam2)


def update_standing(row: dict[str, Any], gf: int, ga: int) -> None:
    row["p"] += 1
    row["gf"] += gf
    row["ga"] += ga
    row["gd"] = row["gf"] - row["ga"]
    if gf > ga:
        row["w"] += 1
        row["pts"] += 3
    elif gf == ga:
        row["d"] += 1
        row["pts"] += 1
    else:
        row["l"] += 1


def rank_rows(rows: list[dict[str, Any]], ratings: dict[str, float], rng: random.Random) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            row.get("pts", 0),
            row.get("gd", 0),
            row.get("gf", 0),
            ratings.get(row["team"], NEUTRAL_ELO),
            rng.random(),
        ),
        reverse=True,
    )


def simulate_groups(
    base: dict[str, dict[str, dict[str, Any]]],
    games: list[dict[str, Any]],
    ratings: dict[str, float],
    rng: random.Random,
) -> tuple[dict[str, list[str]], list[tuple[str, str, dict[str, Any]]]]:
    trial_groups = deepcopy(base)
    scheduled_groups: set[str] = set()
    for game in games:
        if str(game.get("type") or "").lower() != "group" or game_finished(game):
            continue
        group_id = str(game.get("group") or "").strip().upper()
        team1, team2 = game_team_names(game)
        if not group_id or not team1 or not team2:
            continue
        if team1 not in trial_groups.get(group_id, {}) or team2 not in trial_groups.get(group_id, {}):
            continue
        scheduled_groups.add(group_id)
        score1, score2 = simulate_score(team1, team2, ratings, rng)
        update_standing(trial_groups[group_id][team1], score1, score2)
        update_standing(trial_groups[group_id][team2], score2, score1)

    for group_id, rows_by_team in trial_groups.items():
        if group_id in scheduled_groups:
            continue
        for team1, team2 in inferred_remaining_group_pairs(list(rows_by_team.values())):
            score1, score2 = simulate_score(team1, team2, ratings, rng)
            update_standing(rows_by_team[team1], score1, score2)
            update_standing(rows_by_team[team2], score2, score1)

    placements: dict[str, list[str]] = {}
    third_rows: list[tuple[str, str, dict[str, Any]]] = []
    for group_id, rows_by_team in sorted(trial_groups.items()):
        ranked = rank_rows(list(rows_by_team.values()), ratings, rng)
        if len(ranked) < 3:
            continue
        placements[group_id] = [row["team"] for row in ranked[:3]]
        third_rows.append((group_id, ranked[2]["team"], ranked[2]))

    qualified_thirds = sorted(
        third_rows,
        key=lambda item: (
            item[2].get("pts", 0),
            item[2].get("gd", 0),
            item[2].get("gf", 0),
            ratings.get(item[1], NEUTRAL_ELO),
            rng.random(),
        ),
        reverse=True,
    )[:8]
    return placements, qualified_thirds


def inferred_remaining_group_pairs(rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    teams = [row["team"] for row in rows]
    if len(teams) < 2:
        return []
    target_matches = len(teams) - 1
    remaining_slots = {
        row["team"]: max(0, target_matches - int_score(row.get("p")))
        for row in rows
    }
    pairs = list(combinations(teams, 2))
    selected = select_pairs_with_degrees(pairs, remaining_slots, 0, [])
    return selected or []


def select_pairs_with_degrees(
    pairs: list[tuple[str, str]],
    slots: dict[str, int],
    index: int,
    selected: list[tuple[str, str]],
) -> list[tuple[str, str]] | None:
    if all(value == 0 for value in slots.values()):
        return selected
    if index >= len(pairs):
        return None
    if sum(slots.values()) > 2 * (len(pairs) - index):
        return None

    team1, team2 = pairs[index]
    if slots.get(team1, 0) > 0 and slots.get(team2, 0) > 0:
        next_slots = dict(slots)
        next_slots[team1] -= 1
        next_slots[team2] -= 1
        chosen = select_pairs_with_degrees(
            pairs,
            next_slots,
            index + 1,
            [*selected, (team1, team2)],
        )
        if chosen is not None:
            return chosen

    return select_pairs_with_degrees(pairs, slots, index + 1, selected)


def slot_team(
    slot: str,
    placements: dict[str, list[str]],
    third_teams: dict[str, str],
    used_thirds: set[str],
) -> str | None:
    text = str(slot or "").strip()
    winner = text.removeprefix("Winner Group ").strip()
    if winner != text:
        return placements.get(winner, [None])[0]

    runner = text.removeprefix("Runner-up Group ").strip()
    if runner != text:
        teams = placements.get(runner, [])
        return teams[1] if len(teams) > 1 else None

    if text.startswith("3rd Group "):
        candidates = [
            group
            for group in text.removeprefix("3rd Group ").replace("/", " ").split()
            if group
        ]
        for group in candidates:
            if group in third_teams and group not in used_thirds:
                used_thirds.add(group)
                return third_teams[group]
        for group, team in third_teams.items():
            if group not in used_thirds:
                used_thirds.add(group)
                return team
    return normalize_team_name(text) if text and "Match" not in text and "???" not in text else None


def knockout_win_probability(team1: str, team2: str, ratings: dict[str, float]) -> float:
    rating1 = ratings.get(team1, NEUTRAL_ELO)
    rating2 = ratings.get(team2, NEUTRAL_ELO)
    return 1.0 / (1.0 + 10 ** ((rating2 - rating1) / 400.0))


def knockout_winner(team1: str, team2: str, ratings: dict[str, float], rng: random.Random) -> str:
    return team1 if rng.random() < knockout_win_probability(team1, team2, ratings) else team2


def simulate_knockouts(
    r32_matches: list[dict[str, Any]],
    placements: dict[str, list[str]],
    qualified_thirds: list[tuple[str, str, dict[str, Any]]],
    ratings: dict[str, float],
    rng: random.Random,
) -> dict[str, list[str]]:
    third_teams = {group: team for group, team, _ in qualified_thirds}
    used_thirds: set[str] = set()
    r32_pairs: list[tuple[str, str]] = []
    for match in r32_matches:
        team1 = slot_team(match.get("team1", ""), placements, third_teams, used_thirds)
        team2 = slot_team(match.get("team2", ""), placements, third_teams, used_thirds)
        if team1 and team2 and team1 != team2:
            r32_pairs.append((team1, team2))

    stage_winners: dict[str, list[str]] = {"r16": [], "qf": [], "sf": [], "final": [], "win": []}
    current_pairs = r32_pairs
    for stage in ("r16", "qf", "sf", "final", "win"):
        winners = [knockout_winner(team1, team2, ratings, rng) for team1, team2 in current_pairs]
        stage_winners[stage] = winners
        current_pairs = [
            (winners[index], winners[index + 1])
            for index in range(0, len(winners) - 1, 2)
        ]
    return stage_winners


def run_tournament_monte_carlo(
    simulation_count: int = DEFAULT_SIMULATION_COUNT,
    seed: int = DEFAULT_SIMULATION_SEED,
    grid_state_path: Path = GRID_STATE_PATH,
    games_cache_path: Path = DEFAULT_GAMES_CACHE,
) -> dict[str, Any]:
    if simulation_count <= 0:
        raise ValueError("simulation_count must be positive")
    grid_state = load_json(grid_state_path)
    games, games_source = fetch_games(games_cache_path)
    groups = base_groups(grid_state, games)
    teams = sorted({team for group in groups.values() for team in group})
    ratings, rating_meta = build_ratings(teams)
    r32_matches = (grid_state.get("rounds") or [{}])[0].get("matches", [])
    counts = {
        team: {stage: 0 for stage in STAGE_KEYS}
        for team in teams
    }
    rng = random.Random(seed)

    for _ in range(simulation_count):
        placements, qualified_thirds = simulate_groups(groups, games, ratings, rng)
        qualified = {
            team
            for ranked in placements.values()
            for team in ranked[:2]
        } | {team for _, team, _ in qualified_thirds}
        for team in qualified:
            if team in counts:
                counts[team]["group_advancement"] += 1
                counts[team]["r32"] += 1

        knockout_results = simulate_knockouts(
            r32_matches,
            placements,
            qualified_thirds,
            ratings,
            rng,
        )
        for stage, winners in knockout_results.items():
            for team in winners:
                if team in counts:
                    counts[team][stage] += 1

    probabilities = {
        team: {
            stage: round(value / simulation_count, 4)
            for stage, value in stage_counts.items()
        }
        for team, stage_counts in counts.items()
    }

    generated_at = utc_now()
    return {
        "metadata": {
            "method": "random_trial_monte_carlo",
            "model_version": MODEL_VERSION,
            "simulation_count": simulation_count,
            "seed": seed,
            "generated_at_utc": generated_at,
            **rating_meta,
            "schedule_source": games_source,
            "group_count": len(groups),
            "team_count": len(teams),
        },
        "probabilities": probabilities,
    }
