"""Generate safe last-minute briefing artifacts for active fixtures.

Default mode is a dry run. Use --write only after reviewing the manifest.
This script never writes summary.json or metrics.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.common.team_identity import canonical_team_slug
from src.pipeline.discover_active_fixtures import (
    DEFAULT_CACHE_PATH,
    DEFAULT_FORECAST,
    LIVE_GAMES_URL,
    fetch_games,
    game_team_names,
    is_unresolved_team,
    manifest_path,
    match_id_for,
    parse_date_arg,
    parse_game_datetime,
    parse_now_arg,
)

DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "matches"
GENERATOR = "generate_match_briefings.py"
SCHEMA_VERSION = "1.0"
EXPECTED_TEAM_METRIC_FIELDS = (
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
)


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now() -> str:
    return utc_now_dt().isoformat().replace("+00:00", "Z")


def to_utc_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def load_json_payload(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_fixture_datetime(meta: dict[str, Any]) -> datetime | None:
    date_value = str(meta.get("date") or "").strip()
    time_value = str(meta.get("time") or "00:00").strip()
    for fmt in ("%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(f"{date_value} {time_value}", fmt)
        except ValueError:
            pass
    return None


def is_live_game_finished(game: dict[str, Any] | None, now_value: datetime) -> bool:
    if not game:
        return False
    value = game.get("finished")
    if value is True or str(value).upper() == "TRUE":
        return True
    kickoff = parse_game_datetime(game)
    return bool(kickoff and kickoff.date() < now_value.date())


def build_live_index(
    games: list[dict[str, Any]],
    now_value: datetime,
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for game in games:
        team1, team2 = game_team_names(game)
        if is_unresolved_team(team1) or is_unresolved_team(team2):
            continue
        match_id = match_id_for(team1, team2)
        kickoff = parse_game_datetime(game)
        is_finished = is_live_game_finished(game, now_value)
        index[match_id] = {
            "game": game,
            "source_game_id": str(game.get("id") or ""),
            "source_status": "finished" if is_finished else "not_finished",
            "kickoff": kickoff,
        }
    return index


def local_fixture_records(data_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not data_dir.exists():
        return records

    for folder in sorted(data_dir.iterdir()):
        if not folder.is_dir() or not folder.name.endswith("_2026"):
            continue
        summary_path = folder / "summary.json"
        metrics_path = folder / "metrics.json"
        if not summary_path.exists():
            continue
        summary = load_json_payload(summary_path)
        meta = summary.get("metadata", {})
        records.append(
            {
                "match_id": folder.name,
                "folder": folder,
                "summary_path": summary_path,
                "metrics_path": metrics_path,
                "briefing_path": folder / "briefing.json",
                "summary": summary,
                "metadata": meta,
                "kickoff": parse_fixture_datetime(meta),
            }
        )
    return records


def select_records(
    records: list[dict[str, Any]],
    match_id: str | None,
    active_date: datetime.date,
) -> list[dict[str, Any]]:
    if match_id:
        return [record for record in records if record["match_id"] == match_id]
    return [
        record
        for record in records
        if record["kickoff"] and record["kickoff"].date() == active_date
    ]


def briefing_window(
    records: list[dict[str, Any]],
    active_date: datetime.date,
    window_hours: int,
) -> dict[str, Any]:
    kickoffs = [
        record["kickoff"]
        for record in records
        if record["kickoff"] and record["kickoff"].date() == active_date
    ]
    first_kickoff = min(kickoffs) if kickoffs else None
    window_start = first_kickoff - timedelta(hours=window_hours) if first_kickoff else None
    return {
        "active_date": active_date.isoformat(),
        "first_kickoff": first_kickoff.isoformat(timespec="minutes") if first_kickoff else None,
        "window_start": window_start.isoformat(timespec="minutes") if window_start else None,
        "window_hours": window_hours,
    }


def window_is_open(window: dict[str, Any], now_value: datetime) -> bool:
    if not window["first_kickoff"] or not window["window_start"]:
        return False
    first_kickoff = datetime.fromisoformat(window["first_kickoff"])
    window_start = datetime.fromisoformat(window["window_start"])
    return window_start <= now_value <= first_kickoff


def forecast_status(metrics: dict[str, Any]) -> str:
    forecast = metrics.get("dixon_coles_forecast")
    if not isinstance(forecast, dict) or not forecast:
        return "missing"
    for key, expected_value in DEFAULT_FORECAST.items():
        actual_value = forecast.get(key)
        if actual_value is None or abs(float(actual_value) - expected_value) > 0.00001:
            return "model"
    return "default"


def team_metrics_status(
    metrics: dict[str, Any],
    team1: str,
    team2: str,
) -> tuple[str, list[str]]:
    team_metrics = metrics.get("team_metrics")
    if not isinstance(team_metrics, dict):
        return "missing", ["team_metrics object is missing."]

    statuses: list[str] = []
    warnings: list[str] = []
    for team in (team1, team2):
        values = team_metrics.get(team)
        if not isinstance(values, dict) or not values:
            statuses.append("missing")
            warnings.append(f"{team} team_metrics are empty.")
            continue
        missing_fields = [
            field for field in EXPECTED_TEAM_METRIC_FIELDS if field not in values
        ]
        if missing_fields:
            statuses.append("partial")
            warnings.append(
                f"{team} team_metrics missing fields: {', '.join(missing_fields)}."
            )
        else:
            statuses.append("complete")

    if all(status == "complete" for status in statuses):
        return "complete", warnings
    if all(status == "missing" for status in statuses):
        return "missing", warnings
    return "partial", warnings


def existing_fresh_briefing(path: Path, now_utc: datetime) -> bool:
    if not path.exists():
        return False
    try:
        payload = load_json_payload(path)
    except Exception:
        return False
    metadata = payload.get("metadata", {})
    if metadata.get("freshness") != "fresh":
        return False
    valid_until = str(metadata.get("valid_until_utc") or "").strip()
    if not valid_until:
        return True
    try:
        parsed = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed >= now_utc


def source_record(
    name: str,
    path_or_url: str,
    label: str,
    status: str,
    checked_at_utc: str,
    collection_method: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "path_or_url": path_or_url,
        "label": label,
        "status": status,
        "checked_at_utc": checked_at_utc,
        "collection_method": collection_method,
    }


def baseline_injury_notes(summary: dict[str, Any], team1: str, team2: str) -> list[str]:
    injuries = summary.get("ai_summary", {}).get("injuries", {})
    notes: list[str] = []
    for team in (team1, team2):
        slug = canonical_team_slug(team)
        values = injuries.get(slug, [])
        if values:
            joined = "; ".join(str(value) for value in values)
            notes.append(f"{team}: baseline note only - {joined}")
        else:
            notes.append(f"{team}: no baseline injury note available.")
    return notes


def build_briefing_payload(
    record: dict[str, Any],
    metrics: dict[str, Any],
    source: dict[str, Any],
    live_info: dict[str, Any],
    freshness: str,
    window: dict[str, Any],
    now_utc: datetime,
    window_hours: int,
    warnings: list[str],
    blocked_reasons: list[str],
) -> dict[str, Any]:
    summary = record["summary"]
    meta = record["metadata"]
    team1 = str(meta.get("team1") or "")
    team2 = str(meta.get("team2") or "")
    forecast = metrics.get("dixon_coles_forecast", {})
    score_probabilities = metrics.get("score_probabilities", [])
    checked_at_utc = to_utc_z(now_utc)
    tactical_insights = summary.get("ai_summary", {}).get("tactical_insights", [])

    return {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "match_id": record["match_id"],
            "generated_at_utc": checked_at_utc,
            "generator": GENERATOR,
            "mode": "last_minute_briefing",
            "freshness": freshness,
            "valid_until_utc": to_utc_z(now_utc + timedelta(hours=window_hours)),
            "briefing_window_hours": window_hours,
        },
        "fixture": {
            "team1": team1,
            "team2": team2,
            "date": meta.get("date"),
            "time": meta.get("time"),
            "venue": meta.get("venue"),
            "stage": meta.get("stage"),
            "source_game_id": live_info.get("source_game_id"),
        },
        "team_keys": {
            "team1": canonical_team_slug(team1),
            "team2": canonical_team_slug(team2),
        },
        "briefing": {
            "headline": f"Last-minute briefing draft for {team1} vs {team2}",
            "short_context": (
                "Generated from local baseline summary, local metrics, and live "
                "schedule lifecycle validation. Source-backed injury, lineup, "
                "and tactical research has not run yet."
            ),
            "injury_watch": baseline_injury_notes(summary, team1, team2),
            "tactical_updates": [
                "No source-backed tactical update was collected in this run.",
            ],
            "three_keys": [str(value) for value in tactical_insights[:3]],
            "operator_notes": [
                "Treat baseline notes as editorial context, not fresh matchday news.",
                "Run T-036 source-backed research before approving current claims.",
            ],
        },
        "forecast_snapshot": {
            "dixon_coles_forecast": forecast if isinstance(forecast, dict) else {},
            "score_probabilities": score_probabilities
            if isinstance(score_probabilities, list)
            else [],
            "forecast_status": forecast_status(metrics),
        },
        "data_quality": {
            "freshness_state": freshness,
            "team_metrics_status": team_metrics_status(metrics, team1, team2)[0],
            "elo_status": "missing",
            "warnings": warnings,
            "blocked_reasons": blocked_reasons,
            "briefing_window": window,
        },
        "sources": [
            source_record(
                "summary.json",
                manifest_path(record["summary_path"]),
                "static_curated",
                "used",
                checked_at_utc,
                "local_file",
            ),
            source_record(
                "metrics.json",
                manifest_path(record["metrics_path"]),
                "static_curated",
                "used",
                checked_at_utc,
                "local_file",
            ),
            source_record(
                source.get("source_name", "worldcup26.ir games API"),
                source.get("source_url", LIVE_GAMES_URL),
                source.get("source_label", "live_schedule"),
                "used",
                checked_at_utc,
                source.get("collection_method", "api"),
            ),
        ],
        "review": {
            "status": "draft",
            "reviewer": None,
            "reviewed_at_utc": None,
            "notes": "Football Data Scientist approval required before publication.",
        },
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    required_top_level = (
        "metadata",
        "fixture",
        "team_keys",
        "briefing",
        "forecast_snapshot",
        "data_quality",
        "sources",
        "review",
    )
    errors = [key for key in required_top_level if key not in payload]
    metadata = payload.get("metadata", {})
    for key in (
        "schema_version",
        "match_id",
        "generated_at_utc",
        "generator",
        "mode",
        "freshness",
        "valid_until_utc",
        "briefing_window_hours",
    ):
        if key not in metadata:
            errors.append(f"metadata.{key}")
    if not payload.get("sources"):
        errors.append("sources")
    return errors


def process_record(
    record: dict[str, Any],
    source: dict[str, Any],
    live_index: dict[str, dict[str, Any]],
    window: dict[str, Any],
    now_value: datetime,
    now_utc: datetime,
    write: bool,
    force_refresh: bool,
    window_hours: int,
) -> dict[str, Any]:
    match_id = record["match_id"]
    meta = record["metadata"]
    team1 = str(meta.get("team1") or "")
    team2 = str(meta.get("team2") or "")
    live_info = live_index.get(match_id)
    kickoff = record["kickoff"]
    local_date_finished = bool(kickoff and kickoff.date() < now_value.date())
    source_status = (
        live_info["source_status"]
        if live_info
        else "finished" if local_date_finished else "unknown"
    )
    target_path = record["briefing_path"]
    fixture_label = f"{team1} vs {team2}"
    base_action = {
        "match_id": match_id,
        "fixture": fixture_label,
        "target_path": manifest_path(target_path),
        "source_status": source_status,
        "source_game_id": live_info.get("source_game_id") if live_info else None,
    }

    if source_status == "finished":
        return {
            **base_action,
            "status": "skipped",
            "freshness": "skipped",
            "reason": "finished",
            "warnings": [],
            "blocked_reasons": ["finished_fixture"],
        }
    if source_status != "not_finished":
        return {
            **base_action,
            "status": "blocked",
            "freshness": "blocked",
            "reason": "source_status_not_not_finished",
            "warnings": ["Live schedule did not confirm this fixture as not_finished."],
            "blocked_reasons": ["source_status_unknown"],
        }
    if not record["metrics_path"].exists():
        return {
            **base_action,
            "status": "blocked",
            "freshness": "blocked",
            "reason": "missing_metrics_json",
            "warnings": ["metrics.json is required before briefing generation."],
            "blocked_reasons": ["missing_metrics_json"],
        }

    metrics = load_json_payload(record["metrics_path"])
    current_forecast_status = forecast_status(metrics)
    current_team_metrics_status, metric_warnings = team_metrics_status(metrics, team1, team2)
    warnings = [
        "Source-backed news research has not run yet; this artifact is a draft.",
        "Football Data Scientist review is required before approval.",
        "Elo ratings are not stored in metrics.json; runtime Elo remains a separate API augmentation.",
        *metric_warnings,
    ]
    blocked_reasons: list[str] = []
    if current_forecast_status == "default":
        warnings.append("Stored forecast is the default 40/30/30 fallback.")
        blocked_reasons.append("default_forecast")
    elif current_forecast_status == "missing":
        warnings.append("Stored forecast is missing.")
        blocked_reasons.append("missing_forecast")
    if current_team_metrics_status == "missing":
        blocked_reasons.append("empty_team_metrics")

    freshness = "blocked" if blocked_reasons else "fresh"
    if freshness == "fresh" and not window_is_open(window, now_value):
        freshness = "stale"
        warnings.append("Generated outside the configured jornada briefing window.")

    if existing_fresh_briefing(target_path, now_utc) and not force_refresh:
        return {
            **base_action,
            "status": "preserved",
            "freshness": "fresh",
            "reason": "existing_fresh_briefing",
            "warnings": warnings,
            "blocked_reasons": blocked_reasons,
        }

    payload = build_briefing_payload(
        record=record,
        metrics=metrics,
        source=source,
        live_info=live_info,
        freshness=freshness,
        window=window,
        now_utc=now_utc,
        window_hours=window_hours,
        warnings=warnings,
        blocked_reasons=blocked_reasons,
    )
    validation_errors = validate_payload(payload)
    if validation_errors:
        return {
            **base_action,
            "status": "blocked",
            "freshness": "blocked",
            "reason": "schema_validation_failed",
            "warnings": warnings,
            "blocked_reasons": [*blocked_reasons, *validation_errors],
        }

    exists = target_path.exists()
    if not write:
        return {
            **base_action,
            "status": "would_update" if exists else "would_create",
            "freshness": freshness,
            "warnings": warnings,
            "blocked_reasons": blocked_reasons,
            "validation": {"status": "pass"},
        }

    write_json(target_path, payload)
    return {
        **base_action,
        "status": "updated" if exists else "created",
        "freshness": freshness,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "validation": {"status": "pass"},
    }


def build_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    now_value = parse_now_arg(args.now)
    now_utc = utc_now_dt()
    active_date = args.active_date or now_value.date()
    try:
        games, source = fetch_games(args.cache_path)
    except Exception as exc:
        return {
            "task": "T-032",
            "mode": "write" if args.write else "dry_run",
            "generated_at_utc": utc_now(),
            "source": {
                "status": "blocked",
                "source_label": "blocked",
                "source_url": LIVE_GAMES_URL,
                "fallback_path": str(args.cache_path),
                "reason": str(exc),
            },
            "selection": {
                "active_date": active_date.isoformat(),
                "match_id": args.match_id,
                "window_hours": args.window_hours,
                "now": now_value.isoformat(timespec="minutes"),
                "data_dir": str(args.data_dir),
            },
            "counts": {"blocked": 1},
            "actions": [],
        }, 1

    records = local_fixture_records(args.data_dir)
    selected = select_records(records, args.match_id, active_date)
    selected.sort(key=lambda record: record["kickoff"] or datetime.max)
    if args.match_id and selected and not args.active_date and selected[0]["kickoff"]:
        active_date = selected[0]["kickoff"].date()
    live_index = build_live_index(games, now_value)
    window = briefing_window(records, active_date, args.window_hours)
    window["is_open"] = window_is_open(window, now_value)

    actions = [
        process_record(
            record=record,
            source=source,
            live_index=live_index,
            window=window,
            now_value=now_value,
            now_utc=now_utc,
            write=args.write,
            force_refresh=args.force_refresh,
            window_hours=args.window_hours,
        )
        for record in selected
    ]
    if args.match_id and not actions:
        actions.append(
            {
                "match_id": args.match_id,
                "status": "blocked",
                "freshness": "blocked",
                "reason": "match_id_not_found",
                "source_status": "unknown",
                "warnings": ["No local baseline fixture folder was found."],
                "blocked_reasons": ["missing_baseline_folder"],
            }
        )

    counts: dict[str, int] = {}
    for action in actions:
        counts[action["status"]] = counts.get(action["status"], 0) + 1

    return {
        "task": "T-032",
        "mode": "write" if args.write else "dry_run",
        "generated_at_utc": utc_now(),
        "source": source,
        "selection": {
            "active_date": active_date.isoformat(),
            "match_id": args.match_id,
            "window_hours": args.window_hours,
            "now": now_value.isoformat(timespec="minutes"),
            "data_dir": str(args.data_dir),
            "force_refresh": args.force_refresh,
        },
        "briefing_window": window,
        "counts": counts,
        "actions": actions,
    }, 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate safe last-minute briefing.json artifacts."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Accepted for readability; dry run is already the default.",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Create or update briefing.json files. Omit for dry run.",
    )
    parser.add_argument(
        "--window-hours",
        type=int,
        default=3,
        help="Freshness window before the first kickoff of the active jornada.",
    )
    parser.add_argument(
        "--active-date",
        type=parse_date_arg,
        help="Process local fixtures on a schedule date, YYYY-MM-DD or MM/DD/YYYY.",
    )
    parser.add_argument(
        "--match-id",
        help="Process one canonical match id, e.g. canada_qatar_2026.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Overwrite an existing fresh briefing.json.",
    )
    parser.add_argument(
        "--now",
        help="QA override for current local time, format YYYY-MM-DDTHH:MM.",
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
    if args.window_hours <= 0:
        raise SystemExit("--window-hours must be greater than zero")
    if not args.data_dir.is_absolute():
        args.data_dir = PROJECT_ROOT / args.data_dir
    manifest, exit_code = build_manifest(args)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
