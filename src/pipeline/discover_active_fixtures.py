"""Discover active World Cup fixtures and create safe baseline stubs.

Default mode is a dry run that writes no project files. Use --write only after
reviewing the manifest.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.common.team_identity import (
    canonical_team_slug,
    normalize_team_name,
    team_id_to_name,
)

DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "matches"
LIVE_GAMES_URL = "https://worldcup26.ir/get/games"
DEFAULT_CACHE_PATH = Path("/tmp/games.json")

DEFAULT_FORECAST = {
    "team1_win": 0.40,
    "draw": 0.30,
    "team2_win": 0.30,
    "confidence": 0.70,
}

DEFAULT_SCORE_PROBABILITIES = [
    {"score": "1-0", "probability": 0.15},
    {"score": "1-1", "probability": 0.14},
    {"score": "0-1", "probability": 0.13},
    {"score": "2-1", "probability": 0.10},
    {"score": "0-0", "probability": 0.09},
    {"score": "1-2", "probability": 0.08},
]

UNRESOLVED_TOKENS = (
    "winner",
    "runner-up",
    "runner up",
    "loser",
    "match",
    "???",
    "tbd",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json_payload(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_games(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        games = payload.get("games", [])
    else:
        games = payload
    if not isinstance(games, list):
        return []
    return [game for game in games if isinstance(game, dict)]


def fetch_games(cache_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors: list[str] = []
    try:
        result = subprocess.run(
            ["curl", "-s", "-k", "--max-time", "20", LIVE_GAMES_URL],
            capture_output=True,
            text=True,
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
        games = extract_games(load_json_payload(cache_path))
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

    raise RuntimeError("; ".join(errors) or "no fixture source available")


def parse_game_datetime(game: dict[str, Any]) -> datetime | None:
    local_date = str(game.get("local_date") or "").strip()
    if local_date:
        for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S"):
            try:
                return datetime.strptime(local_date, fmt)
            except ValueError:
                pass

    date_value = str(game.get("date") or "").strip()
    time_value = str(game.get("time") or "00:00").strip()
    if date_value:
        for fmt in ("%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(f"{date_value} {time_value}", fmt)
            except ValueError:
                pass
    return None


def parse_date_arg(value: str) -> datetime.date:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise argparse.ArgumentTypeError("date must be YYYY-MM-DD or MM/DD/YYYY")


def parse_now_arg(value: str | None) -> datetime:
    if not value:
        return datetime.now().replace(microsecond=0)
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise argparse.ArgumentTypeError("now must be YYYY-MM-DDTHH:MM")


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


def is_unresolved_team(name: str) -> bool:
    folded = name.lower().strip()
    return not folded or any(token in folded for token in UNRESOLVED_TOKENS)


def is_finished_game(game: dict[str, Any]) -> bool:
    value = game.get("finished")
    if value is True or str(value).upper() == "TRUE":
        return True
    kickoff = parse_game_datetime(game)
    return bool(kickoff and kickoff.date() < datetime.now().date())


def match_id_for(team1: str, team2: str) -> str:
    return f"{canonical_team_slug(team1)}_{canonical_team_slug(team2)}_2026"


def game_date_time(game: dict[str, Any]) -> tuple[str, str]:
    parsed = parse_game_datetime(game)
    if parsed:
        return parsed.strftime("%m/%d/%Y"), parsed.strftime("%H:%M")

    local_date = str(game.get("local_date") or "").strip()
    parts = local_date.split()
    if len(parts) >= 2:
        return parts[0], parts[1]

    return str(game.get("date") or "Date TBD"), str(game.get("time") or "Time TBD")


def game_venue(game: dict[str, Any]) -> str:
    stadium_name = str(game.get("stadium_name") or "").strip()
    if stadium_name:
        return stadium_name
    stadium_id = str(game.get("stadium_id") or "").strip()
    if stadium_id and stadium_id != "0":
        return f"Stadium {stadium_id}"
    return "Venue TBD"


def game_stage(game: dict[str, Any]) -> str:
    game_type = str(game.get("type") or "").strip().lower()
    group = str(game.get("group") or "").strip()
    if game_type == "group":
        return f"Group Stage - Group {group or 'TBD'}"
    labels = {
        "r32": "Round of 32",
        "r16": "Round of 16",
        "qf": "Quarterfinal",
        "sf": "Semifinal",
        "third": "Third Place",
        "final": "Final",
    }
    return labels.get(game_type, game_type.replace("_", " ").title() or "Stage TBD")


def build_summary_stub(
    match_id: str,
    team1: str,
    team2: str,
    game: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    team1_slug = canonical_team_slug(team1)
    team2_slug = canonical_team_slug(team2)
    date_value, time_value = game_date_time(game)
    return {
        "metadata": {
            "match_id": match_id,
            "team1": team1,
            "team2": team2,
            "date": date_value,
            "time": time_value,
            "venue": game_venue(game),
            "stage": game_stage(game),
        },
        "ai_summary": {
            "key_headline": f"Baseline preview pending for {team1} vs {team2}",
            "injuries": {
                team1_slug: ["No verified baseline injury update is available yet."],
                team2_slug: ["No verified baseline injury update is available yet."],
            },
            "confirmed_tactics": {
                team1_slug: {
                    "formation": "TBD",
                    "philosophy": "Baseline tactical preview pending.",
                    "manager": "TBD",
                },
                team2_slug: {
                    "formation": "TBD",
                    "philosophy": "Baseline tactical preview pending.",
                    "manager": "TBD",
                },
            },
            "tactical_insights": [
                "Baseline preview has not been curated yet.",
                "Run last-minute briefing generation inside the match window for fresh updates.",
                "Treat model and team profile sections as unavailable until metrics are populated.",
            ],
        },
        "data_quality": {
            "status": "baseline_stub",
            "source_label": source["source_label"],
            "sources": [source["source_url"]],
            "warnings": ["Editorial preview pending."],
        },
    }


def build_metrics_stub(team1: str, team2: str, source: dict[str, Any]) -> dict[str, Any]:
    return {
        "dixon_coles_forecast": DEFAULT_FORECAST,
        "score_probabilities": DEFAULT_SCORE_PROBABILITIES,
        "team_metrics": {
            team1: {},
            team2: {},
        },
        "data_quality": {
            "status": "baseline_stub",
            "source_label": source["source_label"],
            "forecast_status": "default_forecast",
            "team_metrics_status": "empty_team_metrics",
            "warnings": [
                "Forecast not generated.",
                "Team metrics not populated.",
            ],
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def manifest_path(path: Path) -> str:
    resolved = path if path.is_absolute() else PROJECT_ROOT / path
    try:
        return str(resolved.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def selected_games(
    games: list[dict[str, Any]],
    active_date: datetime.date | None,
    match_id: str | None,
    window_hours: int,
    now_value: datetime,
) -> list[dict[str, Any]]:
    if match_id:
        matches = []
        for game in games:
            team1, team2 = game_team_names(game)
            if is_unresolved_team(team1) or is_unresolved_team(team2):
                continue
            if match_id_for(team1, team2) == match_id:
                matches.append(game)
        return matches

    if active_date:
        return [
            game for game in games
            if parse_game_datetime(game) and parse_game_datetime(game).date() == active_date
        ]

    window_end = now_value + timedelta(hours=window_hours)
    return [
        game for game in games
        if parse_game_datetime(game)
        and now_value <= parse_game_datetime(game) <= window_end
    ]


def process_game(
    game: dict[str, Any],
    data_dir: Path,
    source: dict[str, Any],
    write: bool,
) -> dict[str, Any]:
    team1, team2 = game_team_names(game)
    source_game_id = str(game.get("id") or "")

    if is_finished_game(game):
        match_id = match_id_for(team1, team2) if team1 and team2 else None
        return {
            "status": "skipped",
            "reason": "finished",
            "source_game_id": source_game_id,
            "match_id": match_id,
            "fixture": f"{team1 or 'TBD'} vs {team2 or 'TBD'}",
            "date_time": " ".join(game_date_time(game)),
            "source_status": "finished",
            "labels": ["live_schedule", "finished"],
        }

    if is_unresolved_team(team1) or is_unresolved_team(team2):
        return {
            "status": "blocked",
            "reason": "unresolved_teams",
            "source_game_id": source_game_id,
            "fixture": f"{team1 or 'TBD'} vs {team2 or 'TBD'}",
            "labels": ["blocked", "missing"],
        }

    match_id = match_id_for(team1, team2)
    folder = data_dir / match_id
    summary_path = folder / "summary.json"
    metrics_path = folder / "metrics.json"
    missing_files = [
        manifest_path(path)
        for path in (summary_path, metrics_path)
        if not path.exists()
    ]

    base_action = {
        "source_game_id": source_game_id,
        "match_id": match_id,
        "fixture": f"{team1} vs {team2}",
        "date_time": " ".join(game_date_time(game)),
        "stage": game_stage(game),
        "labels": ["live_schedule"],
        "missing_files": missing_files,
    }

    if not missing_files:
        return {
            **base_action,
            "status": "exists",
            "labels": ["live_schedule", "static_curated"],
        }

    planned_labels = [
        "live_schedule",
        "missing",
        "baseline_stub",
        "default_forecast",
        "empty_team_metrics",
    ]
    if not write:
        return {
            **base_action,
            "status": "would_create",
            "labels": planned_labels,
        }

    if not summary_path.exists():
        write_json(summary_path, build_summary_stub(match_id, team1, team2, game, source))
    if not metrics_path.exists():
        write_json(metrics_path, build_metrics_stub(team1, team2, source))

    return {
        **base_action,
        "status": "created",
        "labels": planned_labels,
    }


def build_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    try:
        games, source = fetch_games(args.cache_path)
    except Exception as exc:
        return {
            "task": "T-034",
            "mode": "write" if args.write else "dry_run",
            "generated_at_utc": utc_now(),
            "source": {
                "status": "blocked",
                "source_label": "blocked",
                "source_url": LIVE_GAMES_URL,
                "fallback_path": str(args.cache_path),
                "reason": str(exc),
            },
            "actions": [],
            "counts": {"blocked": 1},
        }, 1

    now_value = parse_now_arg(args.now)
    games_in_scope = selected_games(
        games=games,
        active_date=args.active_date,
        match_id=args.match_id,
        window_hours=args.window_hours,
        now_value=now_value,
    )
    games_in_scope.sort(key=lambda game: parse_game_datetime(game) or datetime.max)

    actions = [
        process_game(game, args.data_dir, source, args.write)
        for game in games_in_scope
    ]
    if args.match_id and not actions:
        actions.append({
            "status": "blocked",
            "reason": "match_id_not_found_or_unresolved",
            "match_id": args.match_id,
            "labels": ["blocked", "missing"],
        })

    counts: dict[str, int] = {}
    for action in actions:
        counts[action["status"]] = counts.get(action["status"], 0) + 1

    return {
        "task": "T-034",
        "mode": "write" if args.write else "dry_run",
        "generated_at_utc": utc_now(),
        "source": source,
        "selection": {
            "active_date": args.active_date.isoformat() if args.active_date else None,
            "match_id": args.match_id,
            "window_hours": args.window_hours,
            "now": now_value.isoformat(timespec="minutes"),
            "data_dir": str(args.data_dir),
        },
        "counts": counts,
        "actions": actions,
    }, 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover active fixtures and safely create baseline stubs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Accepted for readability; dry run is already the default.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create missing summary.json and metrics.json files. Omit for dry run.",
    )
    parser.add_argument(
        "--window-hours",
        type=int,
        default=24,
        help="Default dry-run/write window when --active-date and --match-id are omitted.",
    )
    parser.add_argument(
        "--active-date",
        type=parse_date_arg,
        help="Process all fixtures on a local schedule date, YYYY-MM-DD or MM/DD/YYYY.",
    )
    parser.add_argument(
        "--match-id",
        help="Process one canonical match id, e.g. brazil_haiti_2026.",
    )
    parser.add_argument(
        "--now",
        help="QA override for the next-window start, format YYYY-MM-DDTHH:MM.",
    )
    parser.add_argument(
        "--cache-path",
        type=Path,
        default=DEFAULT_CACHE_PATH,
        help="Fallback games JSON path when the live API is unavailable.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Fixture data directory. Defaults to data/matches.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.data_dir.is_absolute():
        args.data_dir = PROJECT_ROOT / args.data_dir
    manifest, exit_code = build_manifest(args)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
