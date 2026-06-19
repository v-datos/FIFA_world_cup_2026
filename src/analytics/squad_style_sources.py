"""Cache-backed squad and style metric source records for T-038."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_PATH = (
    PROJECT_ROOT / "data" / "source_cache" / "squad_style" / "latest_metrics.json"
)
PARSER_VERSION = "squad_style_static_manifest_v1"


def _number_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_squad_style_cache(cache_path: Path = DEFAULT_CACHE_PATH) -> dict[str, Any] | None:
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _fixture_matches(row: dict[str, Any], match_id: str) -> bool:
    fixture_ids = row.get("fixture_ids")
    if not fixture_ids:
        return True
    return match_id in fixture_ids


def _normalize_source_record(
    team: str,
    field: str,
    record: dict[str, Any],
    metadata: dict[str, Any],
    previous_value: float | None,
) -> dict[str, Any] | None:
    value = _number_or_none(record.get("value"))
    if value is None:
        return None

    source_label = record.get("source_label") or metadata.get("source_label", "web_researched")
    status = record.get("status", "available")
    return {
        "team": team,
        "field": field,
        "value": value,
        "unit": record.get("unit"),
        "status": status,
        "source_status": "source_backed" if source_label == "web_researched" else status,
        "source_label": source_label,
        "source_name": record.get("source_name") or metadata.get("source_name"),
        "source_url": record.get("source_url") or metadata.get("source_url"),
        "source_path": record.get("source_path"),
        "source_value_text": record.get("source_value_text"),
        "checked_at_utc": record.get("checked_at_utc") or metadata.get("checked_at_utc"),
        "retrieval_method": record.get("retrieval_method") or metadata.get("collection_method"),
        "approximation": bool(record.get("approximation", False)),
        "approximation_note": record.get("approximation_note"),
        "previous_static_value": previous_value,
        "overrode_static_value": previous_value is not None and abs(previous_value - value) > 0.0001,
    }


def apply_squad_style_source_cache(
    metrics_data: dict[str, Any],
    match_id: str,
    teams: tuple[str, str],
    required_fields: list[str],
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    """Merge cached source-backed fields into runtime metrics and return provenance."""
    cache = load_squad_style_cache(cache_path)
    if not cache:
        return {
            "metadata": {
                "status": "missing_cache",
                "source_label": "missing",
                "cache_path": relative_path(cache_path),
                "message": "Squad/style source cache is missing or unreadable.",
            },
            "teams": {},
        }

    metadata = cache.get("metadata", {})
    by_team = {
        normalize_team_name(row.get("team")): row
        for row in cache.get("teams", [])
        if isinstance(row, dict) and row.get("team") and _fixture_matches(row, match_id)
    }
    matched_teams = sorted(by_team)
    required = set(required_fields)
    team_metrics = metrics_data.setdefault("team_metrics", {})
    source_records: dict[str, dict[str, Any]] = {}

    for team in teams:
        normalized_team = normalize_team_name(team)
        row = by_team.get(normalized_team)
        if not row:
            continue
        values = team_metrics.setdefault(normalized_team, {})
        if not isinstance(values, dict):
            values = {}
            team_metrics[normalized_team] = values
        for field, record in (row.get("fields") or {}).items():
            if field not in required or not isinstance(record, dict):
                continue
            previous_value = _number_or_none(values.get(field))
            source_record = _normalize_source_record(
                normalized_team,
                field,
                record,
                metadata,
                previous_value,
            )
            if not source_record:
                continue
            values[field] = source_record["value"]
            source_records.setdefault(normalized_team, {})[field] = source_record

    return {
        "metadata": {
            "status": metadata.get("status", "unknown"),
            "source_label": metadata.get("source_label", "web_researched"),
            "source_name": metadata.get("source_name"),
            "checked_at_utc": metadata.get("checked_at_utc"),
            "parser_version": metadata.get("parser_version"),
            "cache_path": relative_path(cache_path),
            "teams_with_manifest_rows": matched_teams,
            "teams_with_records": sorted(source_records),
            "field_record_count": sum(len(fields) for fields in source_records.values()),
            "warnings": metadata.get("warnings", []),
            "blocked_reasons": metadata.get("blocked_reasons", []),
        },
        "teams": source_records,
    }


def summarize_squad_style_cache(cache_path: Path = DEFAULT_CACHE_PATH) -> dict[str, Any]:
    cache = load_squad_style_cache(cache_path)
    if not cache:
        return {
            "cache_path": relative_path(cache_path),
            "status": "missing_cache",
            "team_count": 0,
            "field_record_count": 0,
        }
    teams = cache.get("teams", [])
    return {
        "cache_path": relative_path(cache_path),
        "status": cache.get("metadata", {}).get("status", "unknown"),
        "source_label": cache.get("metadata", {}).get("source_label"),
        "checked_at_utc": cache.get("metadata", {}).get("checked_at_utc"),
        "parser_version": cache.get("metadata", {}).get("parser_version", PARSER_VERSION),
        "team_count": len(teams),
        "field_record_count": sum(len((team.get("fields") or {})) for team in teams),
        "teams": [team.get("team") for team in teams if team.get("team")],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the T-038 squad/style source cache.")
    parser.add_argument("--cache-path", type=Path, default=DEFAULT_CACHE_PATH)
    args = parser.parse_args()
    print(json.dumps(summarize_squad_style_cache(args.cache_path), indent=2))


if __name__ == "__main__":
    main()
